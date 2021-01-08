# python3 version 3.7.9
# pip3 version 20.1.1
# interpreter python 3.7
# kivy => pip install kivy
# kivyMD => pip install kivy
# run

import kivy
from kivy.lang import Builder
from kivymd.app import MDApp



from kivy.clock import Clock
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.network.urlrequest import UrlRequest
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from kivymd.theming import ThemableBehavior
from kivymd.uix.list import OneLineIconListItem, MDList
from kivymd.uix.chip import MDChip
from kivymd.toast import toast

from kivymd.uix.menu import MDDropdownMenu

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

import datetime

# for profile
from helpers import profile_KV, TagChip

# for chat page
from helpers import chat_KV, PrivateWindow, GroupWindow, FriendList, WindowManager

kivy.require("2.0.0")


# Use the application default credentials
cred = credentials.Certificate('Chatty/chatty-y-firebase-adminsdk-zb1ow-7b79045fa0.json')
default_app = firebase_admin.initialize_app(cred)

# initialize firestore
db = firestore.client() 


# bottom navigation
screen_helper = """

Screen:
    BoxLayout:
        orientation: 'vertical'
        # MDToolbar:
        #     halign: 'center'
        #     title: 'Chatty'
        #     md_bg_color: .2, .2, .2, 1
        #     specific_text_color: 1, 1, 1, 1
            
        MDBottomNavigation:
            panel_color: .2, .2, .2, 1
            
            MDBottomNavigationItem:
                name: 'screen 1'
                text: 'explore'
                MDLabel:
                    text: 'Explore'
                    halign: 'center'
    
            MDBottomNavigationItem:
                name: 'screen 2'
                id: chatscreen
    
            MDBottomNavigationItem:
                name: 'screen 3'
                id: profilescreen

"""

sm = ScreenManager()
sm.add_widget(PrivateWindow(name='private'))
sm.add_widget(GroupWindow(name='group'))
sm.add_widget(FriendList(name='friends'))

class Chatty(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # profile screen
        self.profilescreen = Builder.load_string(profile_KV)
        self.username = "nilay"
        self.user_ref = db.collection(u'users').document(self.username)
        self.user = self.get_by_username(self.username)
        self.profilescreen.ids.username.text = self.username
        self.profilescreen.ids.fname.text = self.user['fname']
        self.profilescreen.ids.lname.text = self.user['lname']
        self.profilescreen.ids.email.text = self.user['email']
        self.profilescreen.ids.status.text = self.user['status']
        self.profilescreen.ids.bio.text = self.user['bio']
        self.profilescreen.ids.streak.secondary_text = str(self.user['streak'])
        # self.profilescreen.ids.location.secondary_text = self.user['city']
        self.profilescreen.ids.location.secondary_text = "istanbul"
        for t in self.user['tags']:
            self.profilescreen.ids.tag_box.add_widget(TagChip(label=t,icon="coffee"))
        # end profile screen

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.primary_hue ='600'
        self.theme_cls.theme_style="Light"
        self.screen = Builder.load_string(screen_helper)

        # build for profile screen
        menu_items = [{"icon_right": None, "text": "online"},
        {"icon": "mail", "text": "offline"},
        {"icon": "email", "text": "happy"},
        {"icon": "git", "text": "sad"},
        {"icon": "git", "text": "away"},]
        self.menu = MDDropdownMenu(
            caller=self.profilescreen.ids.status,
            items=menu_items,
            position="bottom",
            callback=self.set_item,
            width_mult=3,
        )

        tag_menu_items = [{"text": "coffee"},
        { "text": "coding"},
        {"text": "chilling"},
        {"text": "dancing"},
        {"text": "music"},]
        self.tag_menu = MDDropdownMenu(
            caller=self.profilescreen.ids.tags,
            items=tag_menu_items,
            position="bottom",
            callback=self.set_item_tag,
            width_mult=3,
        )

        self.screen.ids.profilescreen.add_widget(self.profilescreen)
        # end build for profile screen


        # build for chat page
        self.chatscreen = Builder.load_string(chat_KV)
        self.screen.ids.chatscreen.add_widget(self.chatscreen)
        # end build for chat page


        return self.screen

    # functions for profile screen
    def set_item(self, instance):
        def set_item(interval):
            self.profilescreen.ids.status.text = instance.text
        Clock.schedule_once(set_item, 0.3)

    def set_item_tag(self, instance):
        def set_item_tag(interval):
            self.profilescreen.ids.tags.text = instance.text
        Clock.schedule_once(set_item_tag, 0.3)

     # edit profile info
    def update_profile(self,**kwargs):
        print(kwargs)
        user_ref = db.collection(u'users').document(kwargs['username'])
        user_ref.update(kwargs)
        user_ref.update({
            u'timestamp': firestore.SERVER_TIMESTAMP
        })
        toast("updated!")
        
    def new_tag(self):
        tag = self.profilescreen.ids.tags.text
        if len(self.user['tags']) >= 4:
                toast("you can have 4 tags at most :( ")
                return
        if tag:
            self.profilescreen.ids.tag_box.add_widget(TagChip(label=tag,icon="coffee"))
            self.user['tags'].append(tag)
            self.tag_add([tag])
        else:
            toast("type something!")
    
    def hey(self):
        toast("hey")


#####################DATABASE##################
    # get user info
    def get_by_username(self, username):
        doc = db.collection(u'users').where(u'username', u'==',username).stream()
        for d in doc:
            return d.to_dict()

    def tag_add(self,tags):
        user_ref = db.collection(u'users').document(self.username)

        # Atomically add a new tag to the 'tags' array field. you can add multiple.
        user_ref.update({u'tags': firestore.ArrayUnion(tags)})

        user_ref.update({
            u'timestamp': firestore.SERVER_TIMESTAMP
        })

    def tag_remove(self,instance,value):
    #  remove a tag from the 'tags' array field.
        self.profilescreen.ids.tag_box.remove_widget(instance)
        self.user['tags'].remove(value)
        self.user_ref.update({u'tags': firestore.ArrayRemove([value])})
        
        self.user_ref.update({
            u'timestamp': firestore.SERVER_TIMESTAMP
        })
        toast(f"{value} removed")


if __name__ == '__main__':
    Chatty().run()
