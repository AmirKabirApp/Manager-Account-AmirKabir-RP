import requests
import re
import os
import json
import threading
from datetime import datetime
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image, AsyncImage
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle

# =========================================================================
# بخش تنظیمات سیستمی و متغیرهای سراسری
# =========================================================================
# تنظیم نحوه باز شدن کیبورد در اندروید
Window.softinput_mode = "below_target"

# آدرس دیتابیس فایربیس پروژه امیرکبیر
URL_DATABASE = "https://manager-account-amirkabi-be8ac-default-rtdb.firebaseio.com/"

# لینک تصویر پروفایل پیش‌فرض برای تمامی بخش‌ها
LINK_AKSE_PROFILE = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"

# رنگ سبز نئونی مخصوص پروژه
NEON_GREEN = (0, 1, 0.5, 1)

def gereftane_ip_dastgah():
    """
    این تابع آی‌پی عمومی دستگاه را برای ثبت در دیتابیس دریافت می‌کند.
    این کار برای امنیت بیشتر و جلوگیری از ثبت‌نام مکرر انجام می‌شود.
    """
    try:
        response = requests.get('https://api.ipify.org', timeout=8)
        return response.text
    except Exception as e:
        print(f"Log: Moshkel dar daryafte IP: {e}")
        return "ip_namaloom"

# =========================================================================
# اجزای گرافیکی سفارشی (Custom UI Components)
# =========================================================================

class KadrVorudi(TextInput):
    """
    کلاس ورودی متن با کادر ضخیم ۵ پیکسلی و رنگ نئون.
    طراحی شده برای خوانایی حداکثری در محیط پایدروید.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_active = ''
        self.background_color = (0.1, 0.1, 0.1, 0.9) # پس‌زمینه تیره داخل کادر
        self.foreground_color = (1, 1, 1, 1)        # رنگ متن سفید
        self.hint_text_color = (0.7, 0.7, 0.7, 0.8)
        self.font_size = '20sp'
        self.bold = True
        self.size_hint_y = None
        self.height = 85
        self.multiline = False
        self.padding = [15, 28, 15, 10]
        self.cursor_color = NEON_GREEN
        self.write_tab = False
        
        with self.canvas.after:
            Color(*NEON_GREEN)
            # ضخامت کادر دقیقاً روی ۵ تنظیم شده است
            self.khat_dore_kadr = Line(rectangle=(self.x, self.y, self.width, self.height), width=5)
        self.bind(pos=self.be_rooz_resani_khat, size=self.be_rooz_resani_khat)

    def be_rooz_resani_khat(self, *args):
        """به‌روزرسانی موقعیت خط دور کادر هنگام تغییر سایز پنجره"""
        self.khat_dore_kadr.rectangle = (self.x, self.y, self.width, self.height)

# =========================================================================
# مدیریت صفحات و پس‌زمینه اصلی (Master System)
# =========================================================================

class MasterScreen(Screen):
    """
    کلاس پایه برای تمام صفحات که تصویر پس‌زمینه را مدیریت می‌کند.
    این کار باعث جلوگیری از تکرار کد در هر صفحه می‌شود.
    """
    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            # بارگذاری فایل background.jpg به عنوان پس‌زمینه ثابت
            self.bg_rect = Rectangle(source='background.jpg', pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        """تطبیق اندازه پس‌زمینه با اندازه صفحه نمایش"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

# =========================================================================
# صفحه ثبت‌نام (Register Screen)
# =========================================================================

class RegisterScreen(MasterScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.main_float = FloatLayout()
        
        # --- لایه کاور تیره (Dark Cover) برای خوانایی متن ---
        # این بخش همان درخواستی است که داشتی تا متن‌ها با بک‌گراند قاطی نشوند
        self.cover_layout = BoxLayout(size_hint=(0.95, 0.94), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        with self.cover_layout.canvas.before:
            Color(0, 0, 0, 0.8) # رنگ مشکی با غلظت ۸۰ درصد
            self.rect_cover = RoundedRectangle(pos=self.cover_layout.pos, size=self.cover_layout.size, radius=[25,])
        self.cover_layout.bind(pos=self._update_cover, size=self._update_cover)

        # محفظه اسکرول برای فرم‌های طولانی
        self.scroll = ScrollView(size_hint=(1, 1), bar_width=5)
        self.content_box = BoxLayout(orientation='vertical', spacing=18, padding=[30, 40, 30, 40], size_hint_y=None)
        self.content_box.bind(minimum_height=self.content_box.setter('height'))
        
        # عنوان اصلی صفحه
        title_label = Label(text="SABTE NAM-E MASTER", font_size='32sp', bold=True, 
                           size_hint_y=None, height=100, color=NEON_GREEN)
        self.content_box.add_widget(title_label)

        # فیلدهای ورودی اطلاعات (بدون Short Bio طبق درخواست قبلی)
        self.vorudi_ha = {}
        fields_config = [
            ("name", "Nam va Famil Vaghei"),
            ("server", "Name Server (Bedune Fasele)"),
            ("pass", "Password-e Amniti"),
            ("age", "Sen (Faghat Adad)"),
            ("rubika", "ID Rubika (@)"),
            ("tg", "ID Telegram (@)")
        ]
        
        for key, hint in fields_config:
            row = BoxLayout(size_hint_y=None, height=90, spacing=15)
            row.add_widget(AsyncImage(source=LINK_AKSE_PROFILE, size_hint_x=None, width=70))
            inp = KadrVorudi(hint_text=hint)
            if "pass" in key: inp.password = True
            self.vorudi_ha[key] = inp
            row.add_widget(inp)
            self.content_box.add_widget(row)
        
        # دکمه‌های عملیاتی
        self.btn_reg = Button(text="SABTE NAM VA VORUD", background_color=(0, 0.8, 0.4, 1), 
                             bold=True, size_hint_y=None, height=85)
        self.btn_reg.bind(on_release=self.validate_and_register)
        
        self.btn_goto_login = Button(text="Ghablan sabt kardi? VORUD", size_hint_y=None, 
                                    height=60, background_color=(0,0,0,0), color=(0,0.7,1,1))
        self.btn_goto_login.bind(on_release=lambda x: setattr(self.manager, 'current', 'login_screen'))
        
        self.content_box.add_widget(self.btn_reg)
        self.content_box.add_widget(self.btn_goto_login)
        
        self.scroll.add_widget(self.content_box)
        self.cover_layout.add_widget(self.scroll)
        self.main_float.add_widget(self.cover_layout)
        self.add_widget(self.main_float)

    def _update_cover(self, instance, value):
        self.rect_cover.pos = instance.pos
        self.rect_cover.size = instance.size

    def validate_and_register(self, instance):
        """بررسی صحت اطلاعات و ارسال به دیتابیس در یک رشته جداگانه"""
        data = {k: v.text.strip() for k, v in self.vorudi_ha.items()}
        if not all(data.values()):
            self.show_popup("KHATA", "Hameye kadr-ha ra por konid!")
            return
        
        def registration_process():
            try:
                ip_address = gereftane_ip_dastgah()
                user_payload = {**data, "status": "active", "ip": ip_address, "reg_date": str(datetime.now())}
                # ذخیره اطلاعات در مسیر کاربران
                requests.put(f"{URL_DATABASE}users/{data['server']}.json", json=user_payload, timeout=12)
                App.get_running_app().user_data = user_payload
                Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'user_panel'))
            except Exception as error:
                print(f"Error: {error}")
                Clock.schedule_once(lambda dt: self.show_popup("KHATA", "Etesal bargharar nist!"))
        
        threading.Thread(target=registration_process).start()

    def show_popup(self, title, content):
        Popup(title=title, content=Label(text=content), size_hint=(0.8, 0.3)).open()

# =========================================================================
# صفحه ورود (Login Screen)
# =========================================================================

class LoginScreen(MasterScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.float_layer = FloatLayout()
        
        # کاور تیره برای بخش ورود
        self.login_cover = BoxLayout(size_hint=(0.9, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        with self.login_cover.canvas.before:
            Color(0, 0, 0, 0.8)
            self.rect_login = RoundedRectangle(pos=self.login_cover.pos, size=self.login_cover.size, radius=[20,])
        self.login_cover.bind(pos=self._update_login_rect, size=self._update_login_rect)

        inner_box = BoxLayout(orientation='vertical', spacing=25, padding=40)
        inner_box.add_widget(Label(text="VORUD BE MASTER", font_size='38sp', bold=True, color=NEON_GREEN))
        
        self.username_input = KadrVorudi(hint_text="Server Name")
        self.password_input = KadrVorudi(hint_text="Password", password=True)
        
        login_btn = Button(text="VORUD", size_hint_y=None, height=85, background_color=(0, 0.6, 0.9, 1), bold=True)
        login_btn.bind(on_release=self.execute_login)
        
        inner_box.add_widget(self.username_input)
        inner_box.add_widget(self.password_input)
        inner_box.add_widget(login_btn)
        
        self.login_cover.add_widget(inner_box)
        self.float_layer.add_widget(self.login_cover)
        self.add_widget(self.float_layer)

    def _update_login_rect(self, instance, value):
        self.rect_login.pos = instance.pos
        self.rect_login.size = instance.size

    def execute_login(self, instance):
        u = self.username_input.text.strip()
        p = self.password_input.text.strip()
        def auth_thread():
            try:
                response = requests.get(f"{URL_DATABASE}users/{u}.json", timeout=10).json()
                if response and response['pass'] == p:
                    App.get_running_app().user_data = response
                    Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'user_panel'))
                else:
                    Clock.schedule_once(lambda dt: Popup(title="KHATA", content=Label(text="Etelaat Eshtebah!")).open())
            except: pass
        threading.Thread(target=auth_thread).start()

# =========================================================================
# پنل کاربری و مدیریت (User & Admin Panels)
# =========================================================================

class UserPanel(MasterScreen):
    def on_enter(self):
        # دریافت داده‌های کاربر و نمایش در داشبورد
        u_info = App.get_running_app().user_data
        self.display_label.text = f"[b][color=00FF88]DASHBOARD:[/color][/b]\n\n" \
                                f"NAME: {u_info['name']}\n" \
                                f"SERVER: {u_info['server']}\n" \
                                f"STATUS: ONLINE"

    def __init__(self, **kw):
        super().__init__(**kw)
        self.p_float = FloatLayout()
        
        # کاور اطلاعات داشبورد
        self.info_cover = BoxLayout(size_hint=(0.9, 0.5), pos_hint={'center_x': 0.5, 'center_y': 0.55})
        with self.info_cover.canvas.before:
            Color(0, 0, 0, 0.8)
            self.rect_info = RoundedRectangle(pos=self.info_cover.pos, size=self.info_cover.size, radius=[20,])
        self.info_cover.bind(pos=self._up_info, size=self._up_info)

        v_content = BoxLayout(orientation='vertical', padding=20)
        self.display_label = Label(text="", font_size='22sp', markup=True, halign='center')
        v_content.add_widget(AsyncImage(source=LINK_AKSE_PROFILE, size_hint_y=None, height=150))
        v_content.add_widget(self.display_label)
        self.info_cover.add_widget(v_content)
        
        # دکمه ورود به بخش ادمین (مخفی در گوشه)
        admin_trigger = Button(text="ADM", size_hint=(0.2, 0.08), pos_hint={'right':0.98, 'y':0.02}, background_color=(0.6,0,0,1))
        admin_trigger.bind(on_release=self.show_admin_auth)
        
        self.p_float.add_widget(self.info_cover)
        self.p_float.add_widget(admin_trigger)
        self.add_widget(self.p_float)

    def _up_info(self, instance, value):
        self.rect_info.pos = instance.pos
        self.rect_info.size = instance.size

    def show_admin_auth(self, x):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        self.admin_pass = KadrVorudi(hint_text="Admin Code", password=True)
        verify_btn = Button(text="VERIFY", size_hint_y=None, height=70)
        layout.add_widget(self.admin_pass)
        layout.add_widget(verify_btn)
        self.admin_pop = Popup(title="Security", content=layout, size_hint=(0.85, 0.4))
        verify_btn.bind(on_release=self.check_admin)
        self.admin_pop.open()

    def check_admin(self, x):
        if self.admin_pass.text == "41148":
            self.admin_pop.dismiss()
            self.manager.current = 'admin_panel'

class AdminPanel(MasterScreen):
    """بخش مدیریت کاربران برای بن کردن یا آزاد کردن اکانت‌ها"""
    def on_enter(self): self.sync_database()

    def sync_database(self):
        self.list_active.clear_widgets()
        self.list_banned.clear_widgets()
        try:
            db_res = requests.get(f"{URL_DATABASE}users.json", timeout=10).json() or {}
            for uid, details in db_res.items():
                item_row = BoxLayout(size_hint_y=None, height=120, spacing=10, padding=10)
                item_row.add_widget(Label(text=f"USER: {details['name']}\nID: {uid}", font_size='14sp'))
                if details.get('status') == 'active':
                    b_btn = Button(text="BAN", background_color=(1,0,0,1), size_hint_x=0.3)
                    b_btn.bind(on_release=lambda x, i=uid: self.patch_user(i, 'banned'))
                    item_row.add_widget(b_btn)
                    self.list_active.add_widget(item_row)
                else:
                    f_btn = Button(text="FREE", background_color=(0,1,0.5,1), size_hint_x=0.3)
                    f_btn.bind(on_release=lambda x, i=uid: self.patch_user(i, 'active'))
                    item_row.add_widget(f_btn)
                    self.list_banned.add_widget(item_row)
        except: pass

    def patch_user(self, i, s):
        requests.patch(f"{URL_DATABASE}users/{i}.json", json={"status": s})
        self.sync_database()

    def __init__(self, **kw):
        super().__init__(**kw)
        self.main_lay = BoxLayout(orientation='vertical', padding=20)
        self.main_lay.add_widget(Label(text="--- ACTIVE ---", color=NEON_GREEN, size_hint_y=None, height=45))
        s1 = ScrollView(); self.list_active = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        self.list_active.bind(minimum_height=self.list_active.setter('height'))
        s1.add_widget(self.list_active); self.main_lay.add_widget(s1)
        
        self.main_lay.add_widget(Label(text="--- BANNED ---", color=(1,0,0,1), size_hint_y=None, height=45))
        s2 = ScrollView(); self.list_banned = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        self.list_banned.bind(minimum_height=self.list_banned.setter('height'))
        s2.add_widget(self.list_banned); self.main_lay.add_widget(s2)
        
        back_b = Button(text="BACK", size_hint_y=None, height=75, background_color=(0.2,0.2,0.2,1))
        back_b.bind(on_release=lambda x: setattr(self.manager, 'current', 'user_panel'))
        self.main_lay.add_widget(back_b)
        self.add_widget(self.main_lay)

# =========================================================================
# موتور اصلی اجرای برنامه (Main Engine)
# =========================================================================

class AmirkabirSystem(App):
    user_data = {}
    def build(self):
        self.title = "Amirkabir Master System"
        self.screen_manager = ScreenManager(transition=NoTransition())
        self.screen_manager.add_widget(RegisterScreen(name='register_screen'))
        self.screen_manager.add_widget(LoginScreen(name='login_screen'))
        self.screen_manager.add_widget(UserPanel(name='user_panel'))
        self.screen_manager.add_widget(AdminPanel(name='admin_panel'))
        return self.screen_manager

if __name__ == '__main__':
    # شروع چرخه حیات اپلیکیشن امیرکبیر
    AmirkabirSystem().run()
