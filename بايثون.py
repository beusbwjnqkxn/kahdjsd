"""
نظام متجر رقمي احترافي متكامل - ملف واحد
Digital Shop Platform - All-in-One File
Version: 2.0.0
"""

import os
import sys
import json
import sqlite3
import logging
import asyncio
import hashlib
import secrets
import re
import csv
import io
import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, asdict
from enum import Enum
from functools import wraps
from contextlib import contextmanager
import threading
import time

# ==================== الوحدات الخارجية ====================

try:
    from flask import (
        Flask, render_template, request, jsonify, 
        session, redirect, url_for, flash, send_file,
        make_response, abort, g
    )
    from flask_login import (
        LoginManager, UserMixin, login_user, logout_user, 
        login_required, current_user
    )
    from flask_cors import CORS
    from flask_babel import Babel, gettext as _
    from flask_wtf import FlaskForm
    from wtforms import StringField, PasswordField, FloatField, IntegerField, SelectField, TextAreaField, BooleanField, FileField
    from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional
    from werkzeug.security import generate_password_hash, check_password_hash
    from werkzeug.utils import secure_filename
    import pandas as pd
    from telegram import (
        Update, InlineKeyboardButton, InlineKeyboardMarkup,
        ReplyKeyboardMarkup, KeyboardButton, InputFile,
        CallbackQuery, Message, Bot
    )
    from telegram.ext import (
        Application, CommandHandler, CallbackQueryHandler,
        MessageHandler, filters, ContextTypes, ConversationHandler
    )
    from telegram.constants import ParseMode
    import qrcode
    from PIL import Image
    import plotly.graph_objs as go
    import plotly.utils
    import matplotlib.pyplot as plt
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    import redis
    from celery import Celery
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    from prometheus_flask_exporter import PrometheusMetrics
    import bcrypt
    import jwt
    from functools import wraps
    import requests
    import aiohttp
    import asyncio
    
except ImportError as e:
    print(f"❌ Missing required module: {e}")
    print("📦 Please install requirements: pip install -r requirements.txt")
    sys.exit(1)

# ==================== التكوين والإعدادات ====================

class Config:
    """إعدادات النظام الرئيسية"""
    
    # إعدادات التطبيق
    APP_NAME = "Digital Shop Platform"
    APP_VERSION = "2.0.0"
    SECRET_KEY = os.environ.get('SECRET_KEY', ''.join(random.choices(string.ascii_letters + string.digits, k=50)))
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
    
    # إعدادات قاعدة البيانات
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///shop.db')
    DB_NAME = os.environ.get('DB_NAME', 'shop.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # إعدادات Redis
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_ENABLED = os.environ.get('REDIS_ENABLED', 'True').lower() == 'true'
    
    # إعدادات البوت
    BOT_TOKEN = os.environ.get('8519977663:AAEWjz3iYEH5np3K6qwfjPRDgb1faLiJRIs', 'YOUR_BOT_TOKEN_HERE')
    BOT_WEBHOOK_URL = os.environ.get('BOT_WEBHOOK_URL', None)
    BOT_WEBHOOK_PATH = '/webhook'
    BOT_PORT = int(os.environ.get('BOT_PORT', 8443))
    
    # إعدادات الدفع
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', '')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID', '')
    PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET', '')
    PAYPAL_MODE = os.environ.get('PAYPAL_MODE', 'sandbox')
    USDT_WALLET = os.environ.get('USDT_WALLET', '')
    BTC_WALLET = os.environ.get('BTC_WALLET', '')
    ETH_WALLET = os.environ.get('ETH_WALLET', '')
    
    # إعدادات البريد الإلكتروني
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@digitalshop.com')
    
    # إعدادات الأمان
    BCRYPT_ROUNDS = 12
    JWT_SECRET = os.environ.get('JWT_SECRET', SECRET_KEY)
    JWT_EXPIRY_HOURS = 24
    SESSION_TIMEOUT = 3600  # ثانية
    MAX_LOGIN_ATTEMPTS = 5
    RATE_LIMIT = 60  # طلب في الدقيقة
    ENABLE_2FA = os.environ.get('ENABLE_2FA', 'True').lower() == 'true'
    
    # إعدادات التطبيق
    CURRENCY = os.environ.get('CURRENCY', 'USD')
    CURRENCY_SYMBOL = os.environ.get('CURRENCY_SYMBOL', '$')
    DEFAULT_LANGUAGE = os.environ.get('DEFAULT_LANGUAGE', 'ar')
    LANGUAGES = ['ar', 'en', 'fr', 'es']
    TIMEZONE = os.environ.get('TIMEZONE', 'UTC')
    
    # إعدادات الإحالات
    REFERRAL_BONUS = float(os.environ.get('REFERRAL_BONUS', 5.0))
    REFERRAL_DISCOUNT = float(os.environ.get('REFERRAL_DISCOUNT', 10.0))
    MAX_REFERRALS = int(os.environ.get('MAX_REFERRALS', 100))
    
    # إعدادات الكوبونات
    MAX_COUPON_USES = int(os.environ.get('MAX_COUPON_USES', 1))
    COUPON_EXPIRY_DAYS = int(os.environ.get('COUPON_EXPIRY_DAYS', 30))
    
    # إعدادات الطلبات
    ORDER_TIMEOUT = int(os.environ.get('ORDER_TIMEOUT', 600))
    MAX_ORDER_QUANTITY = int(os.environ.get('MAX_ORDER_QUANTITY', 10))
    MIN_ORDER_AMOUNT = float(os.environ.get('MIN_ORDER_AMOUNT', 0))
    
    # إعدادات VIP
    VIP_LEVELS = {
        1: {"name": "برونزي", "min_spent": 0, "discount": 0, "icon": "🥉"},
        2: {"name": "فضي", "min_spent": 100, "discount": 5, "icon": "🥈"},
        3: {"name": "ذهبي", "min_spent": 500, "discount": 10, "icon": "🥇"},
        4: {"name": "بلاتيني", "min_spent": 1000, "discount": 15, "icon": "💎"},
        5: {"name": "ماسي", "min_spent": 5000, "discount": 20, "icon": "👑"},
    }
    
    # صلاحيات النظام
    ROLES = {
        'super_admin': {
            'name': 'مالك النظام',
            'permissions': ['*']  # جميع الصلاحيات
        },
        'admin': {
            'name': 'مدير عام',
            'permissions': ['users.view', 'users.edit', 'products.*', 'orders.*', 'categories.*', 'payments.*', 'settings.*']
        },
        'finance_manager': {
            'name': 'مدير مالي',
            'permissions': ['payments.*', 'transactions.*', 'reports.financial']
        },
        'sales_manager': {
            'name': 'مدير مبيعات',
            'permissions': ['orders.*', 'products.view', 'customers.view']
        },
        'product_manager': {
            'name': 'مدير منتجات',
            'permissions': ['products.*', 'categories.*']
        },
        'content_manager': {
            'name': 'مدير محتوى',
            'permissions': ['content.*', 'announcements.*']
        },
        'support_manager': {
            'name': 'مدير دعم',
            'permissions': ['tickets.*', 'users.view']
        },
        'moderator': {
            'name': 'مشرف',
            'permissions': ['users.view', 'orders.view', 'products.view', 'tickets.respond']
        },
        'staff': {
            'name': 'موظف',
            'permissions': ['orders.view', 'products.view', 'tickets.create']
        }
    }
    
    # إعدادات النسخ الاحتياطي
    BACKUP_ENABLED = os.environ.get('BACKUP_ENABLED', 'True').lower() == 'true'
    BACKUP_INTERVAL = int(os.environ.get('BACKUP_INTERVAL', 86400))  # 24 ساعة
    BACKUP_RETENTION = int(os.environ.get('BACKUP_RETENTION', 30))  # 30 يوم
    BACKUP_PATH = os.environ.get('BACKUP_PATH', './backups')
    
    # إعدادات التخزين المؤقت
    CACHE_TIMEOUT = int(os.environ.get('CACHE_TIMEOUT', 300))
    PRODUCT_CACHE_TIMEOUT = int(os.environ.get('PRODUCT_CACHE_TIMEOUT', 600))
    USER_CACHE_TIMEOUT = int(os.environ.get('USER_CACHE_TIMEOUT', 300))
    
    # إعدادات إضافية
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', './uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'csv', 'xlsx'}
    
    # معرفات المديرين في تيليجرام
    ADMIN_IDS = [int(id.strip()) for id in os.environ.get('ADMIN_IDS', '').split(',') if id.strip()]
    
    # المدير الأساسي
    SUPER_ADMIN_ID = int(os.environ.get('SUPER_ADMIN_ID', 1))
    SUPER_ADMIN_EMAIL = os.environ.get('SUPER_ADMIN_EMAIL', 'admin@digitalshop.com')
    SUPER_ADMIN_PASSWORD = os.environ.get('SUPER_ADMIN_PASSWORD', 'Admin@123')

# ==================== قاعدة البيانات ====================

class Database:
    """إدارة قاعدة البيانات المتكاملة"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.db_name = Config.DB_NAME
        self._init_db()
    
    def _init_db(self):
        """تهيئة قاعدة البيانات"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # ==================== جدول المستخدمين ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT,
                role TEXT DEFAULT 'staff',
                permissions TEXT DEFAULT '{}',
                is_active INTEGER DEFAULT 1,
                is_verified INTEGER DEFAULT 0,
                is_blocked INTEGER DEFAULT 0,
                two_factor_enabled INTEGER DEFAULT 0,
                two_factor_secret TEXT,
                balance REAL DEFAULT 0.0,
                frozen_balance REAL DEFAULT 0.0,
                vip_level INTEGER DEFAULT 1,
                total_spent REAL DEFAULT 0.0,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                referral_count INTEGER DEFAULT 0,
                language TEXT DEFAULT 'ar',
                timezone TEXT DEFAULT 'UTC',
                last_login DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referred_by) REFERENCES users (id)
            )
        ''')
        
        # ==================== جدول الملفات الشخصية ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                avatar TEXT,
                bio TEXT,
                phone TEXT,
                address TEXT,
                city TEXT,
                country TEXT,
                postal_code TEXT,
                website TEXT,
                social_media TEXT,
                notification_settings TEXT,
                privacy_settings TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # ==================== جدول جلسات المستخدمين ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                device_type TEXT,
                is_active INTEGER DEFAULT 1,
                expires_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # ==================== جدول الأقسام ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                description TEXT,
                icon TEXT,
                image TEXT,
                parent_id INTEGER,
                sort_order INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                is_featured INTEGER DEFAULT 0,
                meta_title TEXT,
                meta_description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES categories (id) ON DELETE CASCADE
            )
        ''')
        
        # ==================== جدول المنتجات ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                description TEXT,
                short_description TEXT,
                category_id INTEGER NOT NULL,
                price REAL NOT NULL,
                discount_price REAL,
                quantity INTEGER DEFAULT 0,
                min_quantity INTEGER DEFAULT 1,
                max_quantity INTEGER DEFAULT 10,
                platform TEXT,
                country TEXT,
                product_data TEXT,
                images TEXT,
                files TEXT,
                is_active INTEGER DEFAULT 1,
                is_visible INTEGER DEFAULT 1,
                is_featured INTEGER DEFAULT 0,
                views INTEGER DEFAULT 0,
                purchases INTEGER DEFAULT 0,
                rating REAL DEFAULT 0.0,
                reviews_count INTEGER DEFAULT 0,
                meta_title TEXT,
                meta_description TEXT,
                scheduled_publish DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
            )
        ''')
        
        # ==================== جدول مراجعات المنتجات ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT,
                is_approved INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # ==================== جدول الطلبات ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                discount_amount REAL DEFAULT 0.0,
                coupon_code TEXT,
                status TEXT DEFAULT 'pending',
                payment_method TEXT,
                payment_status TEXT DEFAULT 'pending',
                shipping_address TEXT,
                notes TEXT,
                is_auto_paid INTEGER DEFAULT 0,
                delivered INTEGER DEFAULT 0,
                completed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # ==================== جدول تفاصيل الطلبات ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                price REAL NOT NULL,
                discount REAL DEFAULT 0.0,
                product_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
            )
        ''')
        
        # ==================== جدول المعاملات المالية ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                order_id INTEGER,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                fee REAL DEFAULT 0.0,
                description TEXT,
                status TEXT DEFAULT 'pending',
                reference TEXT,
                payment_method TEXT,
                gateway_response TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE SET NULL
            )
        ''')
        
        # ==================== جدول المدفوعات ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                order_id INTEGER,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                method TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                gateway TEXT,
                gateway_data TEXT,
                proof_image TEXT,
                verified_by INTEGER,
                verified_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE SET NULL,
                FOREIGN KEY (verified_by) REFERENCES users (id)
            )
        ''')
        
        # ==================== جدول التذاكر ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_number TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                category TEXT DEFAULT 'general',
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT DEFAULT 'open',
                priority TEXT DEFAULT 'normal',
                assigned_to INTEGER,
                resolved_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (assigned_to) REFERENCES users (id)
            )
        ''')
        
        # ==================== جدول ردود التذاكر ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ticket_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                is_internal INTEGER DEFAULT 0,
                attachments TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # ==================== جدول الإشعارات ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                type TEXT DEFAULT 'general',
                link TEXT,
                is_read INTEGER DEFAULT 0,
                is_pushed INTEGER DEFAULT 0,
                scheduled_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # ==================== جدول المفضلة ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
                UNIQUE(user_id, product_id)
            )
        ''')
        
        # ==================== جدول الكوبونات ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coupons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                type TEXT DEFAULT 'percentage',
                value REAL NOT NULL,
                min_order REAL DEFAULT 0.0,
                max_discount REAL,
                max_uses INTEGER DEFAULT 1,
                used_count INTEGER DEFAULT 0,
                per_user_limit INTEGER DEFAULT 1,
                start_date DATETIME,
                end_date DATETIME,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ==================== جدول استخدامات الكوبونات ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coupon_uses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coupon_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                order_id INTEGER NOT NULL,
                used_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (coupon_id) REFERENCES coupons (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE
            )
        ''')
        
        # ==================== جدول الإحالات ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                bonus_amount REAL DEFAULT 0.0,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                FOREIGN KEY (referrer_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (referred_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE(referred_id)
            )
        ''')
        
        # ==================== جدول الأكواد الهدايا ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gift_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                amount REAL NOT NULL,
                type TEXT DEFAULT 'balance',
                max_uses INTEGER DEFAULT 1,
                used_count INTEGER DEFAULT 0,
                expires_at DATETIME,
                is_active INTEGER DEFAULT 1,
                created_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # ==================== جدول استخدامات الأكواد ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gift_code_uses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                used_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (code_id) REFERENCES gift_codes (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # ==================== جدول الإعلانات ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS banners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                image TEXT NOT NULL,
                link TEXT,
                position TEXT DEFAULT 'home',
                sort_order INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                start_date DATETIME,
                end_date DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ==================== جدول الحملات التسويقية ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT DEFAULT 'email',
                subject TEXT,
                content TEXT,
                target_audience TEXT,
                sent_count INTEGER DEFAULT 0,
                opened_count INTEGER DEFAULT 0,
                clicked_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'draft',
                scheduled_at DATETIME,
                created_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # ==================== جدول السجلات ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                entity_type TEXT,
                entity_id INTEGER,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
            )
        ''')
        
        # ==================== جدول الإحصائيات اليومية ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE NOT NULL,
                users_count INTEGER DEFAULT 0,
                new_users INTEGER DEFAULT 0,
                active_users INTEGER DEFAULT 0,
                orders_count INTEGER DEFAULT 0,
                completed_orders INTEGER DEFAULT 0,
                pending_orders INTEGER DEFAULT 0,
                revenue REAL DEFAULT 0.0,
                profit REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ==================== جدول الإحصائيات الشهرية ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monthly_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                users_count INTEGER DEFAULT 0,
                orders_count INTEGER DEFAULT 0,
                revenue REAL DEFAULT 0.0,
                profit REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(month, year)
            )
        ''')
        
        # ==================== جدول النسخ الاحتياطية ====================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                size INTEGER DEFAULT 0,
                type TEXT DEFAULT 'full',
                status TEXT DEFAULT 'completed',
                created_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # إنشاء المستخدم المدير الرئيسي
        self.create_super_admin()
        
        # إنشاء الأقسام الافتراضية
        self.create_default_categories()
        
        # إنشاء الكوبونات الافتراضية
        self.create_default_coupons()
    
    def get_connection(self):
        """إنشاء اتصال بقاعدة البيانات"""
        return sqlite3.connect(self.db_name)
    
    def execute_query(self, query, params=(), fetch_one=False, fetch_all=False):
        """تنفيذ استعلام قاعدة البيانات"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            else:
                result = None
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def create_super_admin(self):
        """إنشاء المدير الرئيسي"""
        # التحقق من وجود المدير
        existing = self.execute_query(
            "SELECT id FROM users WHERE username = ?",
            (Config.SUPER_ADMIN_EMAIL,),
            fetch_one=True
        )
        
        if not existing:
            # تشفير كلمة المرور
            password_hash = bcrypt.hashpw(
                Config.SUPER_ADMIN_PASSWORD.encode('utf-8'),
                bcrypt.gensalt(Config.BCRYPT_ROUNDS)
            ).decode('utf-8')
            
            # إنشاء كود إحالة
            referral_code = self.generate_referral_code()
            
            self.execute_query(
                '''INSERT INTO users 
                   (username, email, password_hash, first_name, role, is_active, is_verified, referral_code) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (Config.SUPER_ADMIN_EMAIL, Config.SUPER_ADMIN_EMAIL, password_hash, 
                 'Super', 'super_admin', 1, 1, referral_code)
            )
            
            print("✅ تم إنشاء المدير الرئيسي بنجاح")
    
    def create_default_categories(self):
        """إنشاء الأقسام الافتراضية"""
        categories = [
            {"name": "أرقام تيليجرام", "slug": "telegram-numbers", "icon": "📱"},
            {"name": "أرقام واتساب", "slug": "whatsapp-numbers", "icon": "💬"},
            {"name": "أرقام تفعيل", "slug": "activation-numbers", "icon": "🔑"},
            {"name": "حسابات سوشيال ميديا", "slug": "social-media-accounts", "icon": "🌐"},
            {"name": "حسابات ألعاب", "slug": "gaming-accounts", "icon": "🎮"},
            {"name": "حسابات بريد إلكتروني", "slug": "email-accounts", "icon": "📧"},
            {"name": "منتجات رقمية أخرى", "slug": "digital-products", "icon": "💎"},
        ]
        
        for cat in categories:
            existing = self.execute_query(
                "SELECT id FROM categories WHERE slug = ?",
                (cat['slug'],),
                fetch_one=True
            )
            if not existing:
                self.execute_query(
                    "INSERT INTO categories (name, slug, icon) VALUES (?, ?, ?)",
                    (cat['name'], cat['slug'], cat['icon'])
                )
    
    def create_default_coupons(self):
        """إنشاء الكوبونات الافتراضية"""
        coupons = [
            {"code": "WELCOME10", "type": "percentage", "value": 10, "max_uses": 100},
            {"code": "SAVE20", "type": "percentage", "value": 20, "max_uses": 50},
            {"code": "VIP15", "type": "percentage", "value": 15, "max_uses": 30},
        ]
        
        for coupon in coupons:
            existing = self.execute_query(
                "SELECT id FROM coupons WHERE code = ?",
                (coupon['code'],),
                fetch_one=True
            )
            if not existing:
                self.execute_query(
                    "INSERT INTO coupons (code, type, value, max_uses) VALUES (?, ?, ?, ?)",
                    (coupon['code'], coupon['type'], coupon['value'], coupon['max_uses'])
                )
    
    def generate_referral_code(self):
        """توليد كود إحالة فريد"""
        chars = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choices(chars, k=8))
            existing = self.execute_query(
                "SELECT id FROM users WHERE referral_code = ?",
                (code,),
                fetch_one=True
            )
            if not existing:
                return code
    
    # ==================== عمليات المستخدمين ====================
    
    def create_user(self, username, email, password, first_name, last_name=None, role='staff'):
        """إنشاء مستخدم جديد"""
        # التحقق من عدم وجود المستخدم
        existing = self.execute_query(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email),
            fetch_one=True
        )
        if existing:
            return None
        
        # تشفير كلمة المرور
        password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt(Config.BCRYPT_ROUNDS)
        ).decode('utf-8')
        
        # إنشاء كود إحالة
        referral_code = self.generate_referral_code()
        
        cursor = self.execute_query(
            '''INSERT INTO users 
               (username, email, password_hash, first_name, last_name, role, referral_code) 
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (username, email, password_hash, first_name, last_name, role, referral_code)
        )
        
        # إنشاء الملف الشخصي
        user_id = self.execute_query(
            "SELECT last_insert_rowid()",
            fetch_one=True
        )[0]
        
        self.execute_query(
            "INSERT INTO profiles (user_id) VALUES (?)",
            (user_id,)
        )
        
        return user_id
    
    def get_user(self, user_id=None, username=None, email=None):
        """الحصول على بيانات مستخدم"""
        if user_id:
            result = self.execute_query(
                "SELECT * FROM users WHERE id = ?",
                (user_id,),
                fetch_one=True
            )
        elif username:
            result = self.execute_query(
                "SELECT * FROM users WHERE username = ?",
                (username,),
                fetch_one=True
            )
        elif email:
            result = self.execute_query(
                "SELECT * FROM users WHERE email = ?",
                (email,),
                fetch_one=True
            )
        else:
            return None
        
        if result:
            columns = [description[0] for description in self.execute_query(
                "PRAGMA table_info(users)", fetch_all=True
            )]
            return dict(zip(columns, result))
        return None
    
    def get_users(self, limit=50, offset=0, filters=None):
        """الحصول على قائمة المستخدمين"""
        conditions = ["1=1"]
        params = []
        
        if filters:
            if filters.get('search'):
                conditions.append("(username LIKE ? OR email LIKE ? OR first_name LIKE ? OR last_name LIKE ?)")
                search = f"%{filters['search']}%"
                params.extend([search, search, search, search])
            
            if filters.get('role'):
                conditions.append("role = ?")
                params.append(filters['role'])
            
            if filters.get('is_active') is not None:
                conditions.append("is_active = ?")
                params.append(filters['is_active'])
            
            if filters.get('is_blocked') is not None:
                conditions.append("is_blocked = ?")
                params.append(filters['is_blocked'])
            
            if filters.get('vip_level'):
                conditions.append("vip_level >= ?")
                params.append(filters['vip_level'])
            
            if filters.get('date_from'):
                conditions.append("created_at >= ?")
                params.append(filters['date_from'])
            
            if filters.get('date_to'):
                conditions.append("created_at <= ?")
                params.append(filters['date_to'])
        
        where_clause = " AND ".join(conditions)
        query = f"SELECT * FROM users WHERE {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        results = self.execute_query(query, params, fetch_all=True)
        if results:
            columns = [description[0] for description in self.execute_query(
                "PRAGMA table_info(users)", fetch_all=True
            )]
            return [dict(zip(columns, row)) for row in results]
        return []
    
    def update_user(self, user_id, data):
        """تحديث بيانات مستخدم"""
        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        values = list(data.values()) + [user_id]
        return self.execute_query(
            f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values
        )
    
    def delete_user(self, user_id):
        """حذف مستخدم (تجميد)"""
        return self.execute_query(
            "UPDATE users SET is_active = 0, is_blocked = 1 WHERE id = ?",
            (user_id,)
        )
    
    def verify_user(self, user_id):
        """تأكيد حساب مستخدم"""
        return self.execute_query(
            "UPDATE users SET is_verified = 1 WHERE id = ?",
            (user_id,)
        )
    
    def block_user(self, user_id):
        """حظر مستخدم"""
        return self.execute_query(
            "UPDATE users SET is_blocked = 1 WHERE id = ?",
            (user_id,)
        )
    
    def unblock_user(self, user_id):
        """فك حظر مستخدم"""
        return self.execute_query(
            "UPDATE users SET is_blocked = 0 WHERE id = ?",
            (user_id,)
        )
    
    # ==================== عمليات الرصيد ====================
    
    def add_balance(self, user_id, amount, description="شحن رصيد"):
        """إضافة رصيد لمستخدم"""
        user = self.get_user(user_id=user_id)
        if not user:
            return False
        
        new_balance = user['balance'] + amount
        self.update_user(user_id, {'balance': new_balance})
        
        # تسجيل المعاملة
        transaction_id = self.generate_transaction_id()
        self.execute_query(
            '''INSERT INTO transactions 
               (transaction_id, user_id, type, amount, description, status) 
               VALUES (?, ?, 'deposit', ?, ?, 'completed')''',
            (transaction_id, user_id, amount, description)
        )
        
        return True
    
    def deduct_balance(self, user_id, amount, description="خصم رصيد"):
        """خصم رصيد من مستخدم"""
        user = self.get_user(user_id=user_id)
        if not user or user['balance'] < amount:
            return False
        
        new_balance = user['balance'] - amount
        self.update_user(user_id, {'balance': new_balance})
        
        # تسجيل المعاملة
        transaction_id = self.generate_transaction_id()
        self.execute_query(
            '''INSERT INTO transactions 
               (transaction_id, user_id, type, amount, description, status) 
               VALUES (?, ?, 'withdrawal', ?, ?, 'completed')''',
            (transaction_id, user_id, -amount, description)
        )
        
        return True
    
    def freeze_balance(self, user_id, amount):
        """تجميد رصيد"""
        user = self.get_user(user_id=user_id)
        if not user or user['balance'] < amount:
            return False
        
        self.update_user(user_id, {
            'balance': user['balance'] - amount,
            'frozen_balance': user['frozen_balance'] + amount
        })
        return True
    
    def unfreeze_balance(self, user_id, amount):
        """إلغاء تجميد رصيد"""
        user = self.get_user(user_id=user_id)
        if not user or user['frozen_balance'] < amount:
            return False
        
        self.update_user(user_id, {
            'balance': user['balance'] + amount,
            'frozen_balance': user['frozen_balance'] - amount
        })
        return True
    
    def get_transactions(self, user_id=None, limit=50, offset=0):
        """الحصول على سجل المعاملات المالية"""
        if user_id:
            results = self.execute_query(
                "SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (user_id, limit, offset),
                fetch_all=True
            )
        else:
            results = self.execute_query(
                "SELECT * FROM transactions ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
                fetch_all=True
            )
        
        if results:
            columns = [description[0] for description in self.execute_query(
                "PRAGMA table_info(transactions)", fetch_all=True
            )]
            return [dict(zip(columns, row)) for row in results]
        return []
    
    def generate_transaction_id(self):
        """توليد معرف معاملة فريد"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_part = ''.join(random.choices(string.digits, k=8))
        return f"TXN-{timestamp}-{random_part}"
    
    # ==================== عمليات الأقسام ====================
    
    def get_categories(self, parent_id=None, limit=100):
        """الحصول على الأقسام"""
        if parent_id is None:
            results = self.execute_query(
                "SELECT * FROM categories WHERE parent_id IS NULL AND is_active = 1 ORDER BY sort_order LIMIT ?",
                (limit,),
                fetch_all=True
            )
        else:
            results = self.execute_query(
                "SELECT * FROM categories WHERE parent_id = ? AND is_active = 1 ORDER BY sort_order LIMIT ?",
                (parent_id, limit),
                fetch_all=True
            )
        
        if results:
            columns = [description[0] for description in self.execute_query(
                "PRAGMA table_info(categories)", fetch_all=True
            )]
            return [dict(zip(columns, row)) for row in results]
        return []
    
    def get_category(self, category_id):
        """الحصول على قسم محدد"""
        result = self.execute_query(
            "SELECT * FROM categories WHERE id = ?",
            (category_id,),
            fetch_one=True
        )
        if result:
            columns = [description[0] for description in self.execute_query(
                "PRAGMA table_info(categories)", fetch_all=True
            )]
            return dict(zip(columns, result))
        return None
    
    def add_category(self, name, slug, description=None, icon=None, parent_id=None):
        """إضافة قسم جديد"""
        return self.execute_query(
            '''INSERT INTO categories 
               (name, slug, description, icon, parent_id) 
               VALUES (?, ?, ?, ?, ?)''',
            (name, slug, description, icon, parent_id)
        )
    
    def update_category(self, category_id, data):
        """تحديث قسم"""
        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        values = list(data.values()) + [category_id]
        return self.execute_query(
            f"UPDATE categories SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values
        )
    
    def delete_category(self, category_id):
        """حذف قسم"""
        return self.execute_query(
            "UPDATE categories SET is_active = 0 WHERE id = ?",
            (category_id,)
        )
    
    # ==================== عمليات المنتجات ====================
    
    def add_product(self, data):
        """إضافة منتج جديد"""
        # توليد slug
        if 'slug' not in data:
            data['slug'] = self.generate_slug(data['name'])
        
        # تحويل البيانات إلى JSON
        product_data = json.dumps(data.get('product_data', {}))
        images = json.dumps(data.get('images', []))
        files = json.dumps(data.get('files', []))
        
        cursor = self.execute_query(
            '''INSERT INTO products 
               (name, slug, description, short_description, category_id, price, discount_price,
                quantity, min_quantity, max_quantity, platform, country, product_data, images, files,
                is_active, is_visible, is_featured, scheduled_publish) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (data['name'], data['slug'], data.get('description'), data.get('short_description'),
             data['category_id'], data['price'], data.get('discount_price'), data.get('quantity', 0),
             data.get('min_quantity', 1), data.get('max_quantity', 10), data.get('platform'),
             data.get('country'), product_data, images, files,
             data.get('is_active', 1), data.get('is_visible', 1), data.get('is_featured', 0),
             data.get('scheduled_publish'))
        )
        
        return cursor
    
    def get_products(self, filters=None, limit=50, offset=0):
        """الحصول على قائمة المنتجات"""
        conditions = ["1=1"]
        params = []
        
        if filters:
            if filters.get('category_id'):
                conditions.append("category_id = ?")
                params.append(filters['category_id'])
            
            if filters.get('search'):
                conditions.append("(name LIKE ? OR description LIKE ?)")
                search = f"%{filters['search']}%"
                params.extend([search, search])
            
            if filters.get('min_price') is not None:
                conditions.append("price >= ?")
                params.append(filters['min_price'])
            
            if filters.get('max_price') is not None:
                conditions.append("price <= ?")
                params.append(filters['max_price'])
            
            if filters.get('platform'):
                conditions.append("platform = ?")
                params.append(filters['platform'])
            
            if filters.get('country'):
                conditions.append("country = ?")
                params.append(filters['country'])
            
            if filters.get('is_active') is not None:
                conditions.append("is_active = ?")
                params.append(filters['is_active'])
            
            if filters.get('is_visible') is not None:
                conditions.append("is_visible = ?")
                params.append(filters['is_visible'])
            
            if filters.get('is_featured') is not None:
                conditions.append("is_featured = ?")
                params.append(filters['is_featured'])
        
        where_clause = " AND ".join(conditions)
        query = f"SELECT * FROM products WHERE {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        results = self.execute_query(query, params, fetch_all=True)
        if results:
            columns = [description[0] for description in self.execute_query(
                "PRAGMA table_info(products)", fetch_all=True
            )]
            products = []
            for row in results:
                product = dict(zip(columns, row))
                # تحويل JSON
                if product.get('product_data'):
                    product['product_data'] = json.loads(product['product_data'])
                if product.get('images'):
                    product['images'] = json.loads(product['images'])
                if product.get('files'):
                    product['files'] = json.loads(product['files'])
                products.append(product)
            return products
        return []
    
    def get_product(self, product_id):
        """الحصول على منتج محدد"""
        result = self.execute_query(
            "SELECT * FROM products WHERE id = ?",
            (product_id,),
            fetch_one=True
        )
        if result:
            columns = [description[0] for description in self.execute_query(
                "PRAGMA table_info(products)", fetch_all=True
            )]
            product = dict(zip(columns, result))
            # تحويل JSON
            if product.get('product_data'):
                product['product_data'] = json.loads(product['product_data'])
            if product.get('images'):
                product['images'] = json.loads(product['images'])
            if product.get('files'):
                product['files'] = json.loads(product['files'])
            return product
        return None
    
    def update_product(self, product_id, data):
        """تحديث منتج"""
        # تحويل البيانات إلى JSON
        if 'product_data' in data and data['product_data']:
            data['product_data'] = json.dumps(data['product_data'])
        if 'images' in data and data['images']:
            data['images'] = json.dumps(data['images'])
        if 'files' in data and data['files']:
            data['files'] = json.dumps(data['files'])
        
        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        values = list(data.values()) + [product_id]
        return self.execute_query(
            f"UPDATE products SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values
        )
    
    def delete_product(self, product_id):
        """حذف منتج (تجميد)"""
        return self.execute_query(
            "UPDATE products SET is_active = 0 WHERE id = ?",
            (product_id,)
        )
    
    def generate_slug(self, text):
        """توليد slug من النص"""
        slug = text.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        
        # التأكد من عدم وجود تكرار
        existing = self.execute_query(
            "SELECT id FROM products WHERE slug = ?",
            (slug,),
            fetch_one=True
        )
        if existing:
            slug = f"{slug}-{random.randint(1000, 9999)}"
        
        return slug
    
    # ==================== عمليات الطلبات ====================
    
    def create_order(self, user_id, items, total_amount, payment_method=None, coupon_code=None):
        """إنشاء طلب جديد"""
        order_number = self.generate_order_number()
        
        cursor = self.execute_query(
            '''INSERT INTO orders 
               (order_number, user_id, total_amount, payment_method, coupon_code) 
               VALUES (?, ?, ?, ?, ?)''',
            (order_number, user_id, total_amount, payment_method, coupon_code)
        )
        
        order_id = self.execute_query(
            "SELECT last_insert_rowid()",
            fetch_one=True
        )[0]
        
        # إضافة تفاصيل الطلب
        for item in items:
            product = self.get_product(item['product_id'])
            if product:
                self.execute_query(
                    '''INSERT INTO order_items 
                       (order_id, product_id, quantity, price, product_data) 
                       VALUES (?, ?, ?, ?, ?)''',
                    (order_id, item['product_id'], item.get('quantity', 1), 
                     item['price'], json.dumps(product))
                )
                
                # تقليل كمية المنتج
                new_quantity = max(0, product['quantity'] - item.get('quantity', 1))
                self.update_product(item['product_id'], {'quantity': new_quantity})
        
        # تحديث إحصائيات اليوم
        self.update_daily_stats('orders_count', 1)
        self.update_daily_stats('revenue', total_amount)
        
        return order_number
    
    def get_order(self, order_number):
        """الحصول على طلب محدد"""
        result = self.execute_query(
            "SELECT * FROM orders WHERE order_number = ?",
            (order_number,),
            fetch_one=True
        )
        if result:
            columns = [description[0] for description in self.execute_query(
                "PRAGMA table_info(orders)", fetch_all=True
            )]
            order = dict(zip(columns, result))
            
            # الحصول على تفاصيل الطلب
            items = self.execute_query(
                "SELECT * FROM order_items WHERE order_id = ?",
                (order['id'],),
                fetch_all=True
            )
            if items:
                item_columns = [description[0] for description in self.execute_query(
                    "PRAGMA table_info(order_items)", fetch_all=True
                )]
                order['items'] = []
                for item in items:
                    item_dict = dict(zip(item_columns, item))
                    if item_dict.get('product_data'):
                        item_dict['product_data'] = json.loads(item_dict['product_data'])
                    order['items'].append(item_dict)
            
            return order
        return None
    
    def get_user_orders(self, user_id, limit=20):
        """الحصول على طلبات مستخدم"""
        results = self.execute_query(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
            fetch_all=True
        )
        if results:
            columns = [description[0] for description in self.execute_query(
                "PRAGMA table_info(orders)", fetch_all=True
            )]
            return [dict(zip(columns, row)) for row in results]
        return []
    
    def update_order(self, order_number, data):
        """تحديث حالة طلب"""
        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        if 'status' in data and data['status'] == 'completed':
            data['completed_at'] = datetime.now().isoformat()
        values = list(data.values()) + [order_number]
        return self.execute_query(
            f"UPDATE orders SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE order_number = ?",
            values
        )
    
    def generate_order_number(self):
        """توليد رقم طلب فريد"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        random_part = ''.join(random.choices(string.digits, k=6))
        return f"ORD-{timestamp}-{random_part}"
    
    # ==================== عمليات الإحالات ====================
    
    def process_referral(self, referrer_id, referred_id):
        """معالجة الإحالة"""
        referrer = self.get_user(user_id=referrer_id)
        if not referrer:
            return False
        
        # إضافة مكافأة للمُحيل
        bonus = Config.REFERRAL_BONUS
        self.add_balance(referrer_id, bonus, "مكافأة إحالة مستخدم جديد")
        
        # تحديث عدد الإحالات
        self.update_user(referrer_id, {'referral_count': referrer['referral_count'] + 1})
        
        # تحديث المستخدم الجديد
        self.update_user(referred_id, {'referred_by': referrer_id})
        
        # تسجيل الإحالة
        self.execute_query(
            '''INSERT INTO referrals 
               (referrer_id, referred_id, bonus_amount, status) 
               VALUES (?, ?, ?, 'completed')''',
            (referrer_id, referred_id, bonus)
        )
        
        return True
    
    # ==================== عمليات التذاكر ====================
    
    def create_ticket(self, user_id, subject, message, category='general'):
        """إنشاء تذكرة دعم فني"""
        ticket_number = self.generate_ticket_number()
        
        cursor = self.execute_query(
            '''INSERT INTO tickets 
               (ticket_number, user_id, subject, message, category) 
               VALUES (?, ?, ?, ?, ?)''',
            (ticket_number, user_id, subject, message, category)
        )
        
        return ticket_number
    
    def get_tickets(self, user_id=None, status=None, limit=50):
        """الحصول على التذاكر"""
        conditions = []
        params = []
        
        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)
        
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM tickets WHERE {where_clause} ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        results = self.execute_query(query, params, fetch_all=True)
        if results:
            columns = [description[0] for description in self.execute_query(
                "PRAGMA table_info(tickets)", fetch_all=True
            )]
            return [dict(zip(columns, row)) for row in results]
        return []
    
    def add_ticket_reply(self, ticket_id, user_id, message, is_internal=False):
        """إضافة رد على تذكرة"""
        self.execute_query(
            '''INSERT INTO ticket_replies 
               (ticket_id, user_id, message, is_internal) 
               VALUES (?, ?, ?, ?)''',
            (ticket_id, user_id, message, 1 if is_internal else 0)
        )
        
        # تحديث تاريخ التذكرة
        self.execute_query(
            "UPDATE tickets SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (ticket_id,)
        )
    
    def generate_ticket_number(self):
        """توليد رقم تذكرة فريد"""
        timestamp = datetime.now().strftime("%Y%m%d")
        random_part = ''.join(random.choices(string.digits, k=6))
        return f"TKT-{timestamp}-{random_part}"
    
    # ==================== عمليات الكوبونات ====================
    
    def create_coupon(self, code, type, value, min_order=0, max_uses=1, per_user_limit=1, end_date=None):
        """إنشاء كوبون خصم"""
        return self.execute_query(
            '''INSERT INTO coupons 
               (code, type, value, min_order, max_uses, per_user_limit, end_date) 
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (code.upper(), type, value, min_order, max_uses, per_user_limit, end_date)
        )
    
    def get_coupon(self, code):
        """الحصول على كوبون"""
        result = self.execute_query(
            "SELECT * FROM coupons WHERE code = ? AND is_active = 1",
            (code.upper(),),
            fetch_one=True
        )
        if result:
            columns = [description[0] for description in self.execute_query(
                "PRAGMA table_info(coupons)", fetch_all=True
            )]
            return dict(zip(columns, result))
        return None
    
    def use_coupon(self, coupon_id, user_id, order_id):
        """استخدام كوبون"""
        coupon = self.execute_query(
            "SELECT * FROM coupons WHERE id = ?",
            (coupon_id,),
            fetch_one=True
        )
        if not coupon:
            return False
        
        # التحقق من عدد الاستخدامات
        if coupon[6] >= coupon[5]:  # used_count >= max_uses
            return False
        
        # التحقق من صلاحية التاريخ
        if coupon[7] and coupon[7] < datetime.now().isoformat():
            return False
        
        # تسجيل الاستخدام
        self.execute_query(
            '''INSERT INTO coupon_uses 
               (coupon_id, user_id, order_id) 
               VALUES (?, ?, ?)''',
            (coupon_id, user_id, order_id)
        )
        
        # تحديث عدد الاستخدامات
        self.execute_query(
            "UPDATE coupons SET used_count = used_count + 1 WHERE id = ?",
            (coupon_id,)
        )
        
        return True
    
    # ==================== عمليات المفضلة ====================
    
    def add_favorite(self, user_id, product_id):
        """إضافة منتج للمفضلة"""
        try:
            self.execute_query(
                "INSERT INTO favorites (user_id, product_id) VALUES (?, ?)",
                (user_id, product_id)
            )
            return True
        except:
            return False
    
    def remove_favorite(self, user_id, product_id):
        """إزالة منتج من المفضلة"""
        self.execute_query(
            "DELETE FROM favorites WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        )
        return True
    
    def get_favorites(self, user_id):
        """الحصول على قائمة المفضلة"""
        results = self.execute_query(
            '''SELECT p.* FROM products p 
               JOIN favorites f ON p.id = f.product_id 
               WHERE f.user_id = ? AND p.is_active = 1''',
            (user_id,),
            fetch_all=True
        )
        if results:
            columns = [description[0] for description in self.execute_query(
                "PRAGMA table_info(products)", fetch_all=True
            )]
            products = []
            for row in results:
                product = dict(zip(columns, row))
                if product.get('product_data'):
                    product['product_data'] = json.loads(product['product_data'])
                products.append(product)
            return products
        return []
    
    # ==================== عمليات الإشعارات ====================
    
    def add_notification(self, user_id, title, message, type='general', link=None, scheduled_at=None):
        """إضافة إشعار"""
        return self.execute_query(
            '''INSERT INTO notifications 
               (user_id, title, message, type, link, scheduled_at) 
               VALUES (?, ?, ?, ?, ?, ?)''',
            (user_id, title, message, type, link, scheduled_at)
        )
    
    def get_notifications(self, user_id, unread_only=False):
        """الحصول على إشعارات مستخدم"""
        condition = "user_id = ?" if user_id else "user_id IS NULL"
        if unread_only:
            condition += " AND is_read = 0"
        
        results = self.execute_query(
            f"SELECT * FROM notifications WHERE {condition} ORDER BY created_at DESC LIMIT 50",
            (user_id,) if user_id else (),
            fetch_all=True
        )
        if results:
            columns = [description[0] for description in self.execute_query(
                "PRAGMA table_info(notifications)", fetch_all=True
            )]
            return [dict(zip(columns, row)) for row in results]
        return []
    
    def mark_notification_read(self, notification_id):
        """تحديد إشعار كمقروء"""
        return self.execute_query(
            "UPDATE notifications SET is_read = 1 WHERE id = ?",
            (notification_id,)
        )
    
    # ==================== عمليات الإحصائيات ====================
    
    def update_daily_stats(self, field, value):
        """تحديث الإحصائيات اليومية"""
        today = datetime.now().date().isoformat()
        
        # التحقق من وجود إحصاءات اليوم
        existing = self.execute_query(
            "SELECT id FROM daily_stats WHERE date = ?",
            (today,),
            fetch_one=True
        )
        
        if existing:
            self.execute_query(
                f"UPDATE daily_stats SET {field} = {field} + ? WHERE date = ?",
                (value, today)
            )
        else:
            # إنشاء إحصاءات جديدة
            self.execute_query(
                f"INSERT INTO daily_stats (date, {field}) VALUES (?, ?)",
                (today, value)
            )
    
    def get_stats(self, period='daily'):
        """الحصول على الإحصائيات"""
        if period == 'daily':
            date = datetime.now().date().isoformat()
            result = self.execute_query(
                "SELECT * FROM daily_stats WHERE date = ?",
                (date,),
                fetch_one=True
            )
        elif period == 'weekly':
            date = (datetime.now().date() - timedelta(days=7)).isoformat()
            result = self.execute_query(
                "SELECT SUM(orders_count) as orders, SUM(revenue) as revenue, SUM(new_users) as users FROM daily_stats WHERE date >= ?",
                (date,),
                fetch_one=True
            )
        elif period == 'monthly':
            date = (datetime.now().date() - timedelta(days=30)).isoformat()
            result = self.execute_query(
                "SELECT SUM(orders_count) as orders, SUM(revenue) as revenue, SUM(new_users) as users FROM daily_stats WHERE date >= ?",
                (date,),
                fetch_one=True
            )
        elif period == 'yearly':
            date = (datetime.now().date() - timedelta(days=365)).isoformat()
            result = self.execute_query(
                "SELECT SUM(orders_count) as orders, SUM(revenue) as revenue, SUM(new_users) as users FROM daily_stats WHERE date >= ?",
                (date,),
                fetch_one=True
            )
        else:
            return None
        
        if result:
            return {
                'orders': result[0] if result[0] else 0,
                'revenue': result[1] if result[1] else 0,
                'users': result[2] if result[2] else 0
            }
        return {'orders': 0, 'revenue': 0, 'users': 0}
    
    def get_top_products(self, limit=10):
        """الحصول على أكثر المنتجات مبيعاً"""
        results = self.execute_query(
            '''SELECT p.*, COUNT(oi.id) as sales_count 
               FROM products p 
               LEFT JOIN order_items oi ON p.id = oi.product_id 
               WHERE p.is_active = 1 
               GROUP BY p.id 
               ORDER BY sales_count DESC 
               LIMIT ?''',
            (limit,),
            fetch_all=True
        )
        if results:
            columns = [description[0] for description in self.execute_query(
                "PRAGMA table_info(products)", fetch_all=True
            )] + ['sales_count']
            return [dict(zip(columns, row)) for row in results]
        return []
    
    # ==================== عمليات النسخ الاحتياطي ====================
    
    def backup_database(self):
        """إنشاء نسخة احتياطية من قاعدة البيانات"""
        backup_dir = Config.BACKUP_PATH
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/backup_{timestamp}.db"
        
        conn = self.get_connection()
        backup_conn = sqlite3.connect(backup_file)
        
        conn.backup(backup_conn)
        
        backup_conn.close()
        conn.close()
        
        # تسجيل النسخة الاحتياطية
        size = os.path.getsize(backup_file)
        self.execute_query(
            "INSERT INTO backups (filename, size) VALUES (?, ?)",
            (os.path.basename(backup_file), size)
        )
        
        # حذف النسخ القديمة
        backups = sorted([f for f in os.listdir(backup_dir) if f.endswith('.db')])
        retention_days = Config.BACKUP_RETENTION
        if len(backups) > retention_days:
            for f in backups[:-retention_days]:
                os.remove(os.path.join(backup_dir, f))
        
        return backup_file
    
    def restore_database(self, backup_file):
        """استعادة قاعدة البيانات من نسخة احتياطية"""
        if not os.path.exists(backup_file):
            return False
        
        # إغلاق الاتصالات الحالية
        # استعادة قاعدة البيانات
        import shutil
        shutil.copy2(backup_file, self.db_name)
        return True
    
    def get_backups(self, limit=30):
        """الحصول على قائمة النسخ الاحتياطية"""
        results = self.execute_query(
            "SELECT * FROM backups ORDER BY created_at DESC LIMIT ?",
            (limit,),
            fetch_all=True
        )
        if results:
            columns = [description[0] for description in self.execute_query(
                "PRAGMA table_info(backups)", fetch_all=True
            )]
            return [dict(zip(columns, row)) for row in results]
        return []
    
    # ==================== عمليات الصلاحيات ====================
    
    def get_user_permissions(self, user_id):
        """الحصول على صلاحيات المستخدم"""
        user = self.get_user(user_id=user_id)
        if not user:
            return []
        
        if user['role'] == 'super_admin':
            return ['*']  # جميع الصلاحيات
        
        # الحصول على صلاحيات الدور
        role_permissions = Config.ROLES.get(user['role'], {}).get('permissions', [])
        
        # دمج الصلاحيات المخصصة
        custom_permissions = json.loads(user.get('permissions', '{}'))
        custom_perms = custom_permissions.get('permissions', [])
        
        return list(set(role_permissions + custom_perms))
    
    def has_permission(self, user_id, permission):
        """التحقق من صلاحية المستخدم"""
        if not user_id:
            return False
        
        permissions = self.get_user_permissions(user_id)
        
        if '*' in permissions:
            return True
        
        # التحقق من الصلاحية المطلوبة
        if permission in permissions:
            return True
        
        # التحقق من الصلاحيات الفرعية (مثل products.*)
        for perm in permissions:
            if perm.endswith('.*'):
                base = perm.replace('.*', '')
                if permission.startswith(base):
                    return True
        
        return False
    
    # ==================== عمليات السجلات ====================
    
    def log_activity(self, user_id, action, entity_type=None, entity_id=None, details=None, ip_address=None):
        """تسجيل نشاط المستخدم"""
        return self.execute_query(
            '''INSERT INTO activity_logs 
               (user_id, action, entity_type, entity_id, details, ip_address) 
               VALUES (?, ?, ?, ?, ?, ?)''',
            (user_id, action, entity_type, entity_id, json.dumps(details) if details else None, ip_address)
        )
    
    def get_activity_logs(self, user_id=None, limit=100):
        """الحصول على سجل النشاط"""
        if user_id:
            results = self.execute_query(
                "SELECT * FROM activity_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
                fetch_all=True
            )
        else:
            results = self.execute_query(
                "SELECT * FROM activity_logs ORDER BY created_at DESC LIMIT ?",
                (limit,),
                fetch_all=True
            )
        
        if results:
            columns = [description[0] for description in self.execute_query(
                "PRAGMA table_info(activity_logs)", fetch_all=True
            )]
            logs = []
            for row in results:
                log = dict(zip(columns, row))
                if log.get('details'):
                    log['details'] = json.loads(log['details'])
                logs.append(log)
            return logs
        return []

# ==================== فلاسك - تطبيق الويب ====================

# إنشاء تطبيق Flask
app = Flask(__name__, 
    template_folder='../frontend/admin_panel',
    static_folder='../frontend/static'
)

app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['DEBUG'] = Config.DEBUG
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=Config.SESSION_TIMEOUT)

# تهيئة قاعدة البيانات
db = Database()

# تهيئة إدارة الجلسات
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يرجى تسجيل الدخول أولاً'

@login_manager.user_loader
def load_user(user_id):
    """تحميل المستخدم من الجلسة"""
    user_data = db.get_user(user_id=int(user_id))
    if user_data:
        return User(user_data)
    return None

class User(UserMixin):
    """نموذج المستخدم لفلاسك"""
    def __init__(self, data):
        self.id = data['id']
        self.username = data['username']
        self.email = data['email']
        self.first_name = data['first_name']
        self.last_name = data['last_name']
        self.role = data['role']
        self.is_active = data['is_active']
        self.is_blocked = data['is_blocked']
        self.balance = data['balance']
        self.vip_level = data['vip_level']
        self.data = data
    
    def get_id(self):
        return str(self.id)
    
    def has_permission(self, permission):
        return db.has_permission(self.id, permission)
    
    def is_admin(self):
        return self.role in ['super_admin', 'admin']
    
    def is_super_admin(self):
        return self.role == 'super_admin'

# ==================== ديكورات التحقق ====================

def permission_required(permission):
    """ديكور للتحقق من الصلاحية"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if not current_user.has_permission(permission) and not current_user.is_super_admin():
                flash('⚠️ ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """ديكور للتحقق من صلاحية المدير"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_admin():
            flash('⚠️ هذه الصفحة مخصصة للمديرين فقط', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    """ديكور للتحقق من صلاحية المالك"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_super_admin():
            flash('⚠️ هذه الصفحة مخصصة لمالك النظام فقط', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== مسارات التطبيق ====================

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """صفحة تسجيل الدخول"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_data = db.get_user(email=email)
        
        if user_data and user_data['is_active']:
            if bcrypt.checkpw(password.encode('utf-8'), user_data['password_hash'].encode('utf-8')):
                if user_data['is_blocked']:
                    flash('⚠️ حسابك محظور. يرجى التواصل مع الدعم', 'danger')
                    return render_template('login.html')
                
                user = User(user_data)
                login_user(user, remember=True)
                
                # تحديث آخر تسجيل دخول
                db.update_user(user_data['id'], {
                    'last_login': datetime.now().isoformat()
                })
                
                # تسجيل النشاط
                db.log_activity(
                    user_data['id'],
                    'login',
                    'user',
                    user_data['id'],
                    {'ip': request.remote_addr},
                    request.remote_addr
                )
                
                flash('✅ تم تسجيل الدخول بنجاح', 'success')
                return redirect(url_for('dashboard'))
        
        flash('❌ البريد الإلكتروني أو كلمة المرور غير صحيحة', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """تسجيل الخروج"""
    db.log_activity(
        current_user.id,
        'logout',
        'user',
        current_user.id,
        {'ip': request.remote_addr},
        request.remote_addr
    )
    logout_user()
    flash('👋 تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """لوحة التحكم الرئيسية"""
    # الحصول على الإحصائيات
    daily_stats = db.get_stats('daily')
    weekly_stats = db.get_stats('weekly')
    monthly_stats = db.get_stats('monthly')
    yearly_stats = db.get_stats('yearly')
    
    # عدد المستخدمين
    total_users = len(db.get_users(limit=999999))
    active_users_today = db.execute_query(
        "SELECT COUNT(DISTINCT user_id) FROM activity_logs WHERE DATE(created_at) = DATE('now')",
        fetch_one=True
    )[0] or 0
    
    # عدد الطلبات
    total_orders = db.execute_query("SELECT COUNT(*) FROM orders", fetch_one=True)[0] or 0
    completed_orders = db.execute_query(
        "SELECT COUNT(*) FROM orders WHERE status = 'completed'",
        fetch_one=True
    )[0] or 0
    pending_orders = db.execute_query(
        "SELECT COUNT(*) FROM orders WHERE status = 'pending'",
        fetch_one=True
    )[0] or 0
    
    # أحدث العمليات
    recent_logs = db.get_activity_logs(limit=10)
    
    # أحدث التسجيلات
    recent_users = db.get_users(limit=10)
    
    # أكثر المنتجات مبيعاً
    top_products = db.get_top_products(limit=5)
    
    # أكثر الأقسام نشاطاً
    top_categories = db.execute_query(
        '''SELECT c.name, COUNT(p.id) as product_count 
           FROM categories c 
           LEFT JOIN products p ON c.id = p.category_id 
           WHERE p.is_active = 1 
           GROUP BY c.id 
           ORDER BY product_count DESC 
           LIMIT 5''',
        fetch_all=True
    )
    
    return render_template(
        'dashboard.html',
        daily_stats=daily_stats,
        weekly_stats=weekly_stats,
        monthly_stats=monthly_stats,
        yearly_stats=yearly_stats,
        total_users=total_users,
        active_users_today=active_users_today,
        total_orders=total_orders,
        completed_orders=completed_orders,
        pending_orders=pending_orders,
        recent_logs=recent_logs,
        recent_users=recent_users,
        top_products=top_products,
        top_categories=top_categories,
        currency_symbol=Config.CURRENCY_SYMBOL
    )

@app.route('/users')
@login_required
@permission_required('users.view')
def users():
    """صفحة إدارة المستخدمين"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    # فلترة المستخدمين
    filters = {}
    if request.args.get('search'):
        filters['search'] = request.args.get('search')
    if request.args.get('role'):
        filters['role'] = request.args.get('role')
    if request.args.get('status'):
        filters['is_active'] = 1 if request.args.get('status') == 'active' else 0
    
    users_list = db.get_users(limit=per_page, offset=offset, filters=filters)
    total_users = len(db.get_users(limit=999999, filters=filters))
    
    # الحصول على الأدوار المتاحة
    roles = list(Config.ROLES.keys())
    
    return render_template(
        'users.html',
        users=users_list,
        page=page,
        per_page=per_page,
        total=total_users,
        roles=roles,
        filters=filters
    )

@app.route('/users/<int:user_id>')
@login_required
@permission_required('users.view')
def user_detail(user_id):
    """صفحة تفاصيل المستخدم"""
    user_data = db.get_user(user_id=user_id)
    if not user_data:
        abort(404)
    
    # الحصول على طلبات المستخدم
    orders = db.get_user_orders(user_id, limit=20)
    
    # الحصول على معاملات المستخدم
    transactions = db.get_transactions(user_id, limit=20)
    
    # الحصول على سجل النشاط
    logs = db.get_activity_logs(user_id, limit=50)
    
    return render_template(
        'user_detail.html',
        user=user_data,
        orders=orders,
        transactions=transactions,
        logs=logs,
        currency_symbol=Config.CURRENCY_SYMBOL
    )

@app.route('/users/<int:user_id>/edit', methods=['POST'])
@login_required
@permission_required('users.edit')
def edit_user(user_id):
    """تعديل بيانات المستخدم"""
    user_data = db.get_user(user_id=user_id)
    if not user_data:
        return jsonify({'error': 'User not found'}), 404
    
    data = {}
    
    if request.form.get('first_name'):
        data['first_name'] = request.form.get('first_name')
    if request.form.get('last_name'):
        data['last_name'] = request.form.get('last_name')
    if request.form.get('role'):
        data['role'] = request.form.get('role')
    if request.form.get('vip_level'):
        data['vip_level'] = int(request.form.get('vip_level'))
    
    if request.form.get('is_active') is not None:
        data['is_active'] = 1 if request.form.get('is_active') == 'on' else 0
    if request.form.get('is_blocked') is not None:
        data['is_blocked'] = 1 if request.form.get('is_blocked') == 'on' else 0
    
    db.update_user(user_id, data)
    
    db.log_activity(
        current_user.id,
        'user_edit',
        'user',
        user_id,
        {'changes': data, 'ip': request.remote_addr},
        request.remote_addr
    )
    
    flash('✅ تم تحديث بيانات المستخدم بنجاح', 'success')
    return redirect(url_for('user_detail', user_id=user_id))

@app.route('/users/<int:user_id>/balance', methods=['POST'])
@login_required
@permission_required('finance.edit')
def edit_user_balance(user_id):
    """تعديل رصيد المستخدم"""
    user_data = db.get_user(user_id=user_id)
    if not user_data:
        return jsonify({'error': 'User not found'}), 404
    
    amount = float(request.form.get('amount', 0))
    action = request.form.get('action', 'add')
    description = request.form.get('description', '')
    
    if action == 'add':
        db.add_balance(user_id, amount, description)
    elif action == 'deduct':
        db.deduct_balance(user_id, amount, description)
    elif action == 'set':
        current = user_data['balance']
        if amount > current:
            db.add_balance(user_id, amount - current, description)
        elif amount < current:
            db.deduct_balance(user_id, current - amount, description)
    
    db.log_activity(
        current_user.id,
        'balance_edit',
        'user',
        user_id,
        {'action': action, 'amount': amount, 'description': description, 'ip': request.remote_addr},
        request.remote_addr
    )
    
    flash('✅ تم تعديل الرصيد بنجاح', 'success')
    return redirect(url_for('user_detail', user_id=user_id))

@app.route('/users/<int:user_id>/block', methods=['POST'])
@login_required
@permission_required('users.edit')
def block_user(user_id):
    """حظر المستخدم"""
    db.block_user(user_id)
    db.log_activity(
        current_user.id,
        'user_block',
        'user',
        user_id,
        {'ip': request.remote_addr},
        request.remote_addr
    )
    flash('✅ تم حظر المستخدم بنجاح', 'success')
    return redirect(url_for('user_detail', user_id=user_id))

@app.route('/users/<int:user_id>/unblock', methods=['POST'])
@login_required
@permission_required('users.edit')
def unblock_user(user_id):
    """فك حظر المستخدم"""
    db.unblock_user(user_id)
    db.log_activity(
        current_user.id,
        'user_unblock',
        'user',
        user_id,
        {'ip': request.remote_addr},
        request.remote_addr
    )
    flash('✅ تم فك حظر المستخدم بنجاح', 'success')
    return redirect(url_for('user_detail', user_id=user_id))

@app.route('/products')
@login_required
@permission_required('products.view')
def products():
    """صفحة إدارة المنتجات"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    # فلترة المنتجات
    filters = {}
    if request.args.get('search'):
        filters['search'] = request.args.get('search')
    if request.args.get('category_id'):
        filters['category_id'] = int(request.args.get('category_id'))
    if request.args.get('status'):
        filters['is_active'] = 1 if request.args.get('status') == 'active' else 0
    
    products = db.get_products(filters=filters, limit=per_page, offset=offset)
    total_products = len(db.get_products(filters=filters, limit=999999))
    
    # الحصول على الأقسام
    categories = db.get_categories()
    
    return render_template(
        'products.html',
        products=products,
        categories=categories,
        page=page,
        per_page=per_page,
        total=total_products,
        currency_symbol=Config.CURRENCY_SYMBOL
    )

@app.route('/products/add', methods=['GET', 'POST'])
@login_required
@permission_required('products.add')
def add_product():
    """إضافة منتج جديد"""
    categories = db.get_categories()
    
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'short_description': request.form.get('short_description'),
            'category_id': int(request.form.get('category_id')),
            'price': float(request.form.get('price', 0)),
            'discount_price': float(request.form.get('discount_price', 0)) or None,
            'quantity': int(request.form.get('quantity', 0)),
            'min_quantity': int(request.form.get('min_quantity', 1)),
            'max_quantity': int(request.form.get('max_quantity', 10)),
            'platform': request.form.get('platform'),
            'country': request.form.get('country'),
            'is_active': 1 if request.form.get('is_active') else 0,
            'is_visible': 1 if request.form.get('is_visible') else 0,
            'is_featured': 1 if request.form.get('is_featured') else 0,
            'product_data': request.form.get('product_data', '{}'),
        }
        
        try:
            db.add_product(data)
            db.log_activity(
                current_user.id,
                'product_add',
                'product',
                None,
                {'data': data, 'ip': request.remote_addr},
                request.remote_addr
            )
            flash('✅ تم إضافة المنتج بنجاح', 'success')
            return redirect(url_for('products'))
        except Exception as e:
            flash(f'❌ حدث خطأ: {str(e)}', 'danger')
    
    return render_template(
        'product_add.html',
        categories=categories,
        currency_symbol=Config.CURRENCY_SYMBOL
    )

@app.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('products.edit')
def edit_product(product_id):
    """تعديل المنتج"""
    product = db.get_product(product_id)
    if not product:
        abort(404)
    
    categories = db.get_categories()
    
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'short_description': request.form.get('short_description'),
            'category_id': int(request.form.get('category_id')),
            'price': float(request.form.get('price', 0)),
            'discount_price': float(request.form.get('discount_price', 0)) or None,
            'quantity': int(request.form.get('quantity', 0)),
            'min_quantity': int(request.form.get('min_quantity', 1)),
            'max_quantity': int(request.form.get('max_quantity', 10)),
            'platform': request.form.get('platform'),
            'country': request.form.get('country'),
            'is_active': 1 if request.form.get('is_active') else 0,
            'is_visible': 1 if request.form.get('is_visible') else 0,
            'is_featured': 1 if request.form.get('is_featured') else 0,
            'product_data': request.form.get('product_data', '{}'),
        }
        
        try:
            db.update_product(product_id, data)
            db.log_activity(
                current_user.id,
                'product_edit',
                'product',
                product_id,
                {'changes': data, 'ip': request.remote_addr},
                request.remote_addr
            )
            flash('✅ تم تحديث المنتج بنجاح', 'success')
            return redirect(url_for('products'))
        except Exception as e:
            flash(f'❌ حدث خطأ: {str(e)}', 'danger')
    
    return render_template(
        'product_edit.html',
        product=product,
        categories=categories,
        currency_symbol=Config.CURRENCY_SYMBOL
    )

@app.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
@permission_required('products.delete')
def delete_product(product_id):
    """حذف المنتج"""
    db.delete_product(product_id)
    db.log_activity(
        current_user.id,
        'product_delete',
        'product',
        product_id,
        {'ip': request.remote_addr},
        request.remote_addr
    )
    flash('✅ تم حذف المنتج بنجاح', 'success')
    return redirect(url_for('products'))

@app.route('/orders')
@login_required
@permission_required('orders.view')
def orders():
    """صفحة إدارة الطلبات"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    # الحصول على الطلبات
    results = db.execute_query(
        "SELECT * FROM orders ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (per_page, offset),
        fetch_all=True
    )
    
    if results:
        columns = [description[0] for description in db.execute_query(
            "PRAGMA table_info(orders)", fetch_all=True
        )]
        orders_list = [dict(zip(columns, row)) for row in results]
    else:
        orders_list = []
    
    total_orders = db.execute_query("SELECT COUNT(*) FROM orders", fetch_one=True)[0] or 0
    
    return render_template(
        'orders.html',
        orders=orders_list,
        page=page,
        per_page=per_page,
        total=total_orders,
        currency_symbol=Config.CURRENCY_SYMBOL
    )

@app.route('/orders/<int:order_id>')
@login_required
@permission_required('orders.view')
def order_detail(order_id):
    """صفحة تفاصيل الطلب"""
    result = db.execute_query(
        "SELECT * FROM orders WHERE id = ?",
        (order_id,),
        fetch_one=True
    )
    
    if not result:
        abort(404)
    
    columns = [description[0] for description in db.execute_query(
        "PRAGMA table_info(orders)", fetch_all=True
    )]
    order = dict(zip(columns, result))
    
    # الحصول على تفاصيل الطلب
    items = db.execute_query(
        "SELECT * FROM order_items WHERE order_id = ?",
        (order_id,),
        fetch_all=True
    )
    
    if items:
        item_columns = [description[0] for description in db.execute_query(
            "PRAGMA table_info(order_items)", fetch_all=True
        )]
        order['items'] = []
        for item in items:
            item_dict = dict(zip(item_columns, item))
            if item_dict.get('product_data'):
                item_dict['product_data'] = json.loads(item_dict['product_data'])
            order['items'].append(item_dict)
    
    return render_template(
        'order_detail.html',
        order=order,
        currency_symbol=Config.CURRENCY_SYMBOL
    )

@app.route('/orders/<int:order_id>/update', methods=['POST'])
@login_required
@permission_required('orders.edit')
def update_order(order_id):
    """تحديث حالة الطلب"""
    status = request.form.get('status')
    
    order = db.execute_query(
        "SELECT order_number FROM orders WHERE id = ?",
        (order_id,),
        fetch_one=True
    )
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    db.update_order(order[0], {'status': status})
    
    db.log_activity(
        current_user.id,
        'order_update',
        'order',
        order_id,
        {'status': status, 'ip': request.remote_addr},
        request.remote_addr
    )
    
    flash('✅ تم تحديث حالة الطلب بنجاح', 'success')
    return redirect(url_for('order_detail', order_id=order_id))

@app.route('/categories')
@login_required
@permission_required('categories.view')
def categories():
    """صفحة إدارة الأقسام"""
    categories_list = db.get_categories(limit=100)
    return render_template('categories.html', categories=categories_list)

@app.route('/categories/add', methods=['POST'])
@login_required
@permission_required('categories.add')
def add_category():
    """إضافة قسم جديد"""
    name = request.form.get('name')
    slug = request.form.get('slug')
    description = request.form.get('description')
    icon = request.form.get('icon')
    parent_id = request.form.get('parent_id')
    
    if parent_id:
        parent_id = int(parent_id)
    else:
        parent_id = None
    
    db.add_category(name, slug, description, icon, parent_id)
    
    db.log_activity(
        current_user.id,
        'category_add',
        'category',
        None,
        {'name': name, 'slug': slug, 'ip': request.remote_addr},
        request.remote_addr
    )
    
    flash('✅ تم إضافة القسم بنجاح', 'success')
    return redirect(url_for('categories'))

@app.route('/categories/<int:category_id>/edit', methods=['POST'])
@login_required
@permission_required('categories.edit')
def edit_category(category_id):
    """تعديل القسم"""
    data = {}
    
    if request.form.get('name'):
        data['name'] = request.form.get('name')
    if request.form.get('slug'):
        data['slug'] = request.form.get('slug')
    if request.form.get('description'):
        data['description'] = request.form.get('description')
    if request.form.get('icon'):
        data['icon'] = request.form.get('icon')
    if request.form.get('sort_order'):
        data['sort_order'] = int(request.form.get('sort_order'))
    if request.form.get('is_active') is not None:
        data['is_active'] = 1 if request.form.get('is_active') == 'on' else 0
    
    db.update_category(category_id, data)
    
    db.log_activity(
        current_user.id,
        'category_edit',
        'category',
        category_id,
        {'changes': data, 'ip': request.remote_addr},
        request.remote_addr
    )
    
    flash('✅ تم تحديث القسم بنجاح', 'success')
    return redirect(url_for('categories'))

@app.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@permission_required('categories.delete')
def delete_category(category_id):
    """حذف القسم"""
    db.delete_category(category_id)
    
    db.log_activity(
        current_user.id,
        'category_delete',
        'category',
        category_id,
        {'ip': request.remote_addr},
        request.remote_addr
    )
    
    flash('✅ تم حذف القسم بنجاح', 'success')
    return redirect(url_for('categories'))

@app.route('/payments')
@login_required
@permission_required('payments.view')
def payments():
    """صفحة إدارة المدفوعات"""
    results = db.execute_query(
        "SELECT * FROM payments ORDER BY created_at DESC LIMIT 100",
        fetch_all=True
    )
    
    if results:
        columns = [description[0] for description in db.execute_query(
            "PRAGMA table_info(payments)", fetch_all=True
        )]
        payments_list = [dict(zip(columns, row)) for row in results]
    else:
        payments_list = []
    
    return render_template(
        'payments.html',
        payments=payments_list,
        currency_symbol=Config.CURRENCY_SYMBOL
    )

@app.route('/payments/<int:payment_id>/verify', methods=['POST'])
@login_required
@permission_required('payments.verify')
def verify_payment(payment_id):
    """تأكيد الدفع"""
    payment = db.execute_query(
        "SELECT * FROM payments WHERE id = ?",
        (payment_id,),
        fetch_one=True
    )
    
    if not payment:
        return jsonify({'error': 'Payment not found'}), 404
    
    # تحديث حالة الدفع
    db.execute_query(
        "UPDATE payments SET status = 'completed', verified_by = ?, verified_at = CURRENT_TIMESTAMP WHERE id = ?",
        (current_user.id, payment_id)
    )
    
    # إضافة الرصيد للمستخدم
    db.add_balance(payment[2], payment[3], f"دفع عبر {payment[5]}")
    
    db.log_activity(
        current_user.id,
        'payment_verify',
        'payment',
        payment_id,
        {'ip': request.remote_addr},
        request.remote_addr
    )
    
    flash('✅ تم تأكيد الدفع بنجاح', 'success')
    return redirect(url_for('payments'))

@app.route('/reports')
@login_required
@permission_required('reports.view')
def reports():
    """صفحة التقارير"""
    # الحصول على الإحصائيات
    daily = db.get_stats('daily')
    weekly = db.get_stats('weekly')
    monthly = db.get_stats('monthly')
    yearly = db.get_stats('yearly')
    
    # أكثر المنتجات مبيعاً
    top_products = db.get_top_products(10)
    
    return render_template(
        'reports.html',
        daily=daily,
        weekly=weekly,
        monthly=monthly,
        yearly=yearly,
        top_products=top_products,
        currency_symbol=Config.CURRENCY_SYMBOL
    )

@app.route('/reports/export/<format>/<period>')
@login_required
@permission_required('reports.export')
def export_report(format, period):
    """تصدير التقارير"""
    stats = db.get_stats(period)
    
    # إنشاء بيانات التقرير
    data = {
        'الفترة': period,
        'الطلبات': stats['orders'],
        'الإيرادات': stats['revenue'],
        'المستخدمين': stats['users'],
        'تاريخ التقرير': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    if format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['المؤشر', 'القيمة'])
        for key, value in data.items():
            writer.writerow([key, value])
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=report_{period}.csv'
        return response
    
    elif format == 'pdf':
        # إنشاء PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        styles = getSampleStyleSheet()
        elements.append(Paragraph(f'تقرير {period}', styles['Title']))
        elements.append(Spacer(1, 0.25*inch))
        
        # إنشاء جدول
        table_data = [['المؤشر', 'القيمة']]
        for key, value in data.items():
            table_data.append([key, str(value)])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=report_{period}.pdf'
        return response
    
    return jsonify(data)

@app.route('/settings')
@login_required
@super_admin_required
def settings():
    """صفحة الإعدادات"""
    return render_template('settings.html')

@app.route('/settings/update', methods=['POST'])
@login_required
@super_admin_required
def update_settings():
    """تحديث الإعدادات"""
    # تحديث الإعدادات في ملف البيئة
    # هذا مجرد مثال، في الواقع يجب تحديث قاعدة البيانات
    flash('✅ تم تحديث الإعدادات بنجاح', 'success')
    return redirect(url_for('settings'))

@app.route('/backup')
@login_required
@super_admin_required
def backup():
    """صفحة النسخ الاحتياطي"""
    backups = db.get_backups(30)
    return render_template('backup.html', backups=backups)

@app.route('/backup/create', methods=['POST'])
@login_required
@super_admin_required
def create_backup():
    """إنشاء نسخة احتياطية"""
    backup_file = db.backup_database()
    flash(f'✅ تم إنشاء النسخة الاحتياطية: {os.path.basename(backup_file)}', 'success')
    return redirect(url_for('backup'))

@app.route('/backup/restore', methods=['POST'])
@login_required
@super_admin_required
def restore_backup():
    """استعادة نسخة احتياطية"""
    filename = request.form.get('filename')
    backup_file = os.path.join(Config.BACKUP_PATH, filename)
    
    if db.restore_database(backup_file):
        flash('✅ تم استعادة النسخة الاحتياطية بنجاح', 'success')
    else:
        flash('❌ فشل استعادة النسخة الاحتياطية', 'danger')
    
    return redirect(url_for('backup'))

@app.route('/tickets')
@login_required
@permission_required('tickets.view')
def tickets():
    """صفحة إدارة التذاكر"""
    tickets_list = db.get_tickets(limit=100)
    return render_template('tickets.html', tickets=tickets_list)

@app.route('/tickets/<int:ticket_id>')
@login_required
@permission_required('tickets.view')
def ticket_detail(ticket_id):
    """صفحة تفاصيل التذكرة"""
    ticket = db.execute_query(
        "SELECT * FROM tickets WHERE id = ?",
        (ticket_id,),
        fetch_one=True
    )
    
    if not ticket:
        abort(404)
    
    columns = [description[0] for description in db.execute_query(
        "PRAGMA table_info(tickets)", fetch_all=True
    )]
    ticket_dict = dict(zip(columns, ticket))
    
    # الحصول على الردود
    replies = db.execute_query(
        "SELECT * FROM ticket_replies WHERE ticket_id = ? ORDER BY created_at",
        (ticket_id,),
        fetch_all=True
    )
    
    if replies:
        reply_columns = [description[0] for description in db.execute_query(
            "PRAGMA table_info(ticket_replies)", fetch_all=True
        )]
        replies_list = [dict(zip(reply_columns, row)) for row in replies]
    else:
        replies_list = []
    
    return render_template(
        'ticket_detail.html',
        ticket=ticket_dict,
        replies=replies_list
    )

@app.route('/tickets/<int:ticket_id>/reply', methods=['POST'])
@login_required
@permission_required('tickets.respond')
def reply_ticket(ticket_id):
    """الرد على تذكرة"""
    message = request.form.get('message')
    is_internal = request.form.get('is_internal') == 'on'
    
    db.add_ticket_reply(ticket_id, current_user.id, message, is_internal)
    
    # تحديث حالة التذكرة
    if not is_internal:
        db.execute_query(
            "UPDATE tickets SET status = 'in_progress' WHERE id = ?",
            (ticket_id,)
        )
    
    db.log_activity(
        current_user.id,
        'ticket_reply',
        'ticket',
        ticket_id,
        {'ip': request.remote_addr},
        request.remote_addr
    )
    
    flash('✅ تم إرسال الرد بنجاح', 'success')
    return redirect(url_for('ticket_detail', ticket_id=ticket_id))

@app.route('/tickets/<int:ticket_id>/close', methods=['POST'])
@login_required
@permission_required('tickets.respond')
def close_ticket(ticket_id):
    """إغلاق التذكرة"""
    db.execute_query(
        "UPDATE tickets SET status = 'closed', resolved_at = CURRENT_TIMESTAMP WHERE id = ?",
        (ticket_id,)
    )
    
    db.log_activity(
        current_user.id,
        'ticket_close',
        'ticket',
        ticket_id,
        {'ip': request.remote_addr},
        request.remote_addr
    )
    
    flash('✅ تم إغلاق التذكرة بنجاح', 'success')
    return redirect(url_for('ticket_detail', ticket_id=ticket_id))

@app.route('/notifications')
@login_required
def notifications():
    """صفحة الإشعارات"""
    notifications_list = db.get_notifications(current_user.id)
    return render_template('notifications.html', notifications=notifications_list)

@app.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """تحديد إشعار كمقروء"""
    db.mark_notification_read(notification_id)
    return jsonify({'success': True})

@app.route('/notifications/mark_all_read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """تحديد جميع الإشعارات كمقروءة"""
    notifications = db.get_notifications(current_user.id, unread_only=True)
    for notification in notifications:
        db.mark_notification_read(notification['id'])
    return jsonify({'success': True})

# ==================== خطافات ما قبل الطلب ====================

@app.before_request
def before_request():
    """تنفيذ قبل كل طلب"""
    if current_user.is_authenticated:
        # تسجيل النشاط للطلبات المهمة
        if request.method in ['POST', 'PUT', 'DELETE']:
            db.log_activity(
                current_user.id,
                f"{request.method}_{request.endpoint}",
                None,
                None,
                {'url': request.url, 'ip': request.remote_addr},
                request.remote_addr
            )

# ==================== معالجات الخطأ ====================

@app.errorhandler(404)
def not_found_error(error):
    """صفحة 404"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """صفحة 500"""
    return render_template('500.html'), 500

# ==================== بوت تيليجرام ====================

class TelegramBot:
    """بوت تيليجرام للمتجر"""
    
    def __init__(self):
        self.token = Config.BOT_TOKEN
        self.db = Database()
        self.application = None
        self.setup_handlers()
    
    def setup_handlers(self):
        """إعداد معالجات البوت"""
        self.application = Application.builder().token(self.token).build()
        
        # أوامر المستخدم
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("shop", self.shop_command))
        self.application.add_handler(CommandHandler("balance", self.balance_command))
        self.application.add_handler(CommandHandler("orders", self.orders_command))
        self.application.add_handler(CommandHandler("profile", self.profile_command))
        self.application.add_handler(CommandHandler("support", self.support_command))
        
        # أوامر الإدارة
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        
        # معالج الأزرار
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # معالج الرسائل
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر بدء البوت"""
        user = update.effective_user
        
        # التحقق من وجود المستخدم
        db_user = self.db.get_user(email=f"{user.id}@telegram.com")
        if not db_user:
            # إنشاء مستخدم جديد
            self.db.create_user(
                f"tg_{user.id}",
                f"{user.id}@telegram.com",
                self.generate_password(),
                user.first_name,
                user.last_name
            )
            
            # معالجة الإحالة
            if context.args:
                referral_code = context.args[0]
                referrer = self.db.get_user_by_referral(referral_code)
                if referrer:
                    self.db.process_referral(referrer['id'], user.id)
        
        text = f"""
🌟 **مرحباً بك في {Config.APP_NAME}** 🌟

متجرك الموثوق لشراء الأرقام والحسابات الرقمية.

📌 **الأوامر المتاحة:**
• /shop - عرض المنتجات
• /balance - عرض الرصيد
• /orders - سجل المشتريات
• /profile - الملف الشخصي
• /support - الدعم الفني
• /help - المساعدة

✨ استمتع بتجربة تسوق آمنة وسريعة!
        """
        
        keyboard = [
            [InlineKeyboardButton("🛍️ المتجر", callback_data="shop_main"),
             InlineKeyboardButton("💰 الرصيد", callback_data="balance")],
            [InlineKeyboardButton("📦 طلباتي", callback_data="orders"),
             InlineKeyboardButton("👤 الملف الشخصي", callback_data="profile")],
        ]
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر المساعدة"""
        text = f"""
📚 **دليل استخدام {Config.APP_NAME}**

🔹 **التسوق:**
• استخدم /shop لعرض المنتجات
• اختر القسم المناسب
• اضغط شراء لشراء المنتج

🔹 **الرصيد:**
• استخدم /balance لعرض رصيدك
• يمكنك شحن الرصيد عبر الدعم الفني

🔹 **الطلبات:**
• استخدم /orders لعرض سجل مشترياتك

🔹 **الدعم:**
• استخدم /support للتواصل مع الدعم الفني

🔹 **المعلومات:**
• استخدم /profile لعرض ملفك الشخصي
        """
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    
    async def shop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر عرض المتجر"""
        categories = self.db.get_categories()
        
        text = "🛍️ **المتجر**\n\nاختر القسم:"
        
        keyboard = []
        for cat in categories:
            keyboard.append([InlineKeyboardButton(
                f"{cat.get('icon', '📁')} {cat['name']}",
                callback_data=f"cat_{cat['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")])
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر عرض الرصيد"""
        user_id = update.effective_user.id
        user = self.db.get_user(email=f"{user_id}@telegram.com")
        
        if not user:
            await update.message.reply_text("⚠️ يرجى استخدام /start أولاً")
            return
        
        text = f"""
💰 **الرصيد الحالي**

👤 المستخدم: {user['first_name']}
💵 الرصيد: {Config.CURRENCY_SYMBOL}{user['balance']:.2f}
🔒 الرصيد المجمد: {Config.CURRENCY_SYMBOL}{user['frozen_balance']:.2f}
💎 مستوى VIP: {Config.VIP_LEVELS[user['vip_level']]['name']}
💰 إجمالي المشتريات: {Config.CURRENCY_SYMBOL}{user['total_spent']:.2f}
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 سجل المعاملات", callback_data="transactions")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")],
        ]
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def orders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر عرض الطلبات"""
        user_id = update.effective_user.id
        user = self.db.get_user(email=f"{user_id}@telegram.com")
        
        if not user:
            await update.message.reply_text("⚠️ يرجى استخدام /start أولاً")
            return
        
        orders = self.db.get_user_orders(user['id'])
        
        if not orders:
            await update.message.reply_text("📦 لا توجد طلبات حتى الآن")
            return
        
        text = "📦 **سجل المشتريات**\n\n"
        
        for order in orders[:5]:
            status_emoji = {
                'pending': '⏳',
                'processing': '🔄',
                'completed': '✅',
                'cancelled': '❌',
                'refunded': '🔄'
            }.get(order['status'], '❓')
            
            text += f"{status_emoji} **طلب #{order['order_number']}**\n"
            text += f"💰 المبلغ: {Config.CURRENCY_SYMBOL}{order['total_amount']:.2f}\n"
            text += f"📅 التاريخ: {order['created_at'][:16]}\n"
            text += f"📌 الحالة: {order['status']}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")],
        ]
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر عرض الملف الشخصي"""
        user_id = update.effective_user.id
        user = self.db.get_user(email=f"{user_id}@telegram.com")
        
        if not user:
            await update.message.reply_text("⚠️ يرجى استخدام /start أولاً")
            return
        
        vip_level = Config.VIP_LEVELS[user['vip_level']]
        
        text = f"""
👤 **الملف الشخصي**

🆔 المعرف: {user['id']}
👤 الاسم: {user['first_name']} {user['last_name'] or ''}
📝 البريد الإلكتروني: {user['email']}

💎 مستوى VIP: {vip_level['name']}
🎁 خصم VIP: {vip_level['discount']}%
💰 الرصيد: {Config.CURRENCY_SYMBOL}{user['balance']:.2f}
💸 إجمالي المشتريات: {Config.CURRENCY_SYMBOL}{user['total_spent']:.2f}
⭐ عدد الإحالات: {user['referral_count']}

🔹 **رابط الإحالة:**
https://t.me/{update.effective_chat.username}?start={user['referral_code']}
        """
        
        keyboard = [
            [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")],
        ]
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def support_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر الدعم الفني"""
        text = """
🆘 **مركز الدعم الفني**

📝 **لإنشاء تذكرة دعم:**
أرسل رسالتك بعد هذا الأمر مباشرة:
/support رسالتك هنا

📋 **لمتابعة تذاكرك:**
استخدم /tickets

💬 **للتواصل المباشر:**
استخدم /contact

📌 سيتم الرد عليك في أقرب وقت.
        """
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """لوحة تحكم الإدارة"""
        user_id = update.effective_user.id
        
        if user_id not in Config.ADMIN_IDS:
            await update.message.reply_text("⛔ غير مصرح لك بالدخول إلى لوحة التحكم")
            return
        
        text = """
🔐 **لوحة تحكم الإدارة**

📊 **الإحصائيات:**
• عرض الإحصائيات
• تقارير المبيعات
• تحليلات المستخدمين

📦 **إدارة المنتجات:**
• إضافة منتج
• تعديل منتج
• حذف منتج

👤 **إدارة المستخدمين:**
• عرض المستخدمين
• حظر/فك حظر
• إدارة الرصيد

📋 **إدارة الطلبات:**
• عرض الطلبات
• تحديث الحالات

📢 **الإذاعات:**
• إذاعة للمستخدمين
• إعلانات فورية
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton("📦 المنتجات", callback_data="admin_products")],
            [InlineKeyboardButton("👤 المستخدمين", callback_data="admin_users")],
            [InlineKeyboardButton("📋 الطلبات", callback_data="admin_orders")],
            [InlineKeyboardButton("📢 الإذاعة", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")],
        ]
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الأزرار"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "main_menu":
            await self.show_main_menu(query)
        
        elif data == "shop_main":
            await self.show_shop_menu(query)
        
        elif data.startswith("cat_"):
            category_id = int(data.split("_")[1])
            await self.show_category_products(query, category_id)
        
        elif data.startswith("product_"):
            product_id = int(data.split("_")[1])
            await self.show_product_detail(query, product_id)
        
        elif data.startswith("buy_"):
            product_id = int(data.split("_")[1])
            await self.process_purchase(query, product_id)
        
        elif data.startswith("confirm_buy_"):
            product_id = int(data.split("_")[2])
            await self.confirm_purchase(query, product_id)
        
        elif data == "balance":
            await self.show_balance(query)
        
        elif data == "orders":
            await self.show_orders(query)
        
        elif data == "profile":
            await self.show_profile(query)
        
        elif data == "transactions":
            await self.show_transactions(query)
        
        # أوامر الإدارة
        elif data == "admin_stats":
            await self.admin_stats(query)
        
        elif data == "admin_products":
            await self.admin_products(query)
        
        elif data == "admin_users":
            await self.admin_users(query)
        
        elif data == "admin_orders":
            await self.admin_orders(query)
        
        elif data == "admin_broadcast":
            await self.admin_broadcast(query)
    
    async def show_main_menu(self, query):
        """عرض القائمة الرئيسية"""
        text = f"""
🌟 **{Config.APP_NAME}** 🌟

مرحباً بك في متجرنا!
اختر الخدمة المناسبة:
        """
        
        keyboard = [
            [InlineKeyboardButton("🛍️ المتجر", callback_data="shop_main"),
             InlineKeyboardButton("💰 الرصيد", callback_data="balance")],
            [InlineKeyboardButton("📦 طلباتي", callback_data="orders"),
             InlineKeyboardButton("👤 ملفي الشخصي", callback_data="profile")],
            [InlineKeyboardButton("🆘 الدعم الفني", callback_data="support")],
        ]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_shop_menu(self, query):
        """عرض قائمة المتجر"""
        categories = self.db.get_categories()
        
        text = "🛍️ **المتجر**\n\nاختر القسم:"
        
        keyboard = []
        for cat in categories:
            keyboard.append([InlineKeyboardButton(
                f"{cat.get('icon', '📁')} {cat['name']}",
                callback_data=f"cat_{cat['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")])
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_category_products(self, query, category_id):
        """عرض منتجات القسم"""
        products = self.db.get_products(filters={'category_id': category_id})
        category = self.db.get_category(category_id)
        
        if not products:
            await query.edit_message_text(
                f"📁 **{category['name']}**\n\nلا توجد منتجات في هذا القسم",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 رجوع", callback_data="shop_main")]
                ])
            )
            return
        
        text = f"📁 **{category['name']}**\n\n"
        
        for product in products[:10]:
            text += f"📦 {product['name']}\n"
            text += f"💰 {Config.CURRENCY_SYMBOL}{product['price']:.2f}\n"
            if product.get('country'):
                text += f"🌍 {product['country']}\n"
            text += f"---\n"
        
        keyboard = [
            [InlineKeyboardButton("🔙 رجوع", callback_data="shop_main")],
        ]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_product_detail(self, query, product_id):
        """عرض تفاصيل المنتج"""
        product = self.db.get_product(product_id)
        
        if not product:
            await query.edit_message_text("❌ المنتج غير موجود")
            return
        
        text = f"""
📦 **{product['name']}**

📝 **الوصف:**
{product.get('description', 'لا يوجد وصف')}

💰 **السعر:** {Config.CURRENCY_SYMBOL}{product['price']:.2f}
📦 **الكمية:** {product['quantity']}
🌍 **الدولة:** {product.get('country', 'غير محدد')}
📱 **المنصة:** {product.get('platform', 'غير محدد')}
📊 **المشاهدات:** {product['views']}
🛒 **المبيعات:** {product['purchases']}
        """
        
        keyboard = []
        
        if product['quantity'] > 0:
            keyboard.append([InlineKeyboardButton("🛒 شراء الآن", callback_data=f"buy_{product_id}")])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"cat_{product['category_id']}")])
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def process_purchase(self, query, product_id):
        """معالجة الشراء"""
        user_id = query.from_user.id
        user = self.db.get_user(email=f"{user_id}@telegram.com")
        product = self.db.get_product(product_id)
        
        if not user or not product:
            await query.edit_message_text("❌ حدث خطأ")
            return
        
        if product['quantity'] <= 0:
            await query.edit_message_text("❌ المنتج غير متوفر حالياً")
            return
        
        if user['balance'] < product['price']:
            await query.edit_message_text(
                f"❌ **رصيد غير كافٍ**\n\n"
                f"💰 رصيدك: {Config.CURRENCY_SYMBOL}{user['balance']:.2f}\n"
                f"💵 سعر المنتج: {Config.CURRENCY_SYMBOL}{product['price']:.2f}\n"
                f"🔄 تحتاج: {Config.CURRENCY_SYMBOL}{product['price'] - user['balance']:.2f} إضافية\n\n"
                f"🔹 للشحن، تواصل مع الإدارة عبر /support",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        text = f"""
🛒 **تأكيد الشراء**

📦 المنتج: {product['name']}
💰 السعر: {Config.CURRENCY_SYMBOL}{product['price']:.2f}
💵 رصيدك: {Config.CURRENCY_SYMBOL}{user['balance']:.2f}
💎 الرصيد بعد الشراء: {Config.CURRENCY_SYMBOL}{user['balance'] - product['price']:.2f}

⚠️ هل أنت متأكد من شراء هذا المنتج؟
        """
        
        keyboard = [
            [
                InlineKeyboardButton("✅ تأكيد الشراء", callback_data=f"confirm_buy_{product_id}"),
                InlineKeyboardButton("❌ إلغاء", callback_data=f"product_{product_id}")
            ]
        ]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def confirm_purchase(self, query, product_id):
        """تأكيد الشراء"""
        user_id = query.from_user.id
        user = self.db.get_user(email=f"{user_id}@telegram.com")
        product = self.db.get_product(product_id)
        
        if not user or not product:
            await query.edit_message_text("❌ حدث خطأ")
            return
        
        if product['quantity'] <= 0:
            await query.edit_message_text("❌ المنتج غير متوفر حالياً")
            return
        
        if user['balance'] < product['price']:
            await query.edit_message_text("❌ رصيد غير كافٍ")
            return
        
        # تجميد الرصيد
        self.db.freeze_balance(user['id'], product['price'])
        
        try:
            # إنشاء الطلب
            items = [{
                'product_id': product_id,
                'quantity': 1,
                'price': product['price']
            }]
            
            order_number = self.db.create_order(
                user['id'],
                items,
                product['price']
            )
            
            # خصم الرصيد
            self.db.deduct_balance(user['id'], product['price'], f"شراء: {product['name']}")
            self.db.unfreeze_balance(user['id'], product['price'])
            
            # تحديث إحصائيات المنتج
            self.db.update_product(product_id, {'purchases': product['purchases'] + 1})
            
            # عرض تفاصيل المنتج
            product_data = product.get('product_data')
            if product_data:
                if isinstance(product_data, dict):
                    details = json.dumps(product_data, indent=2, ensure_ascii=False)
                else:
                    details = product_data
            else:
                details = f"📦 {product['name']}\n🆔 {product['id']}"
            
            await query.edit_message_text(
                f"✅ **تم الشراء بنجاح!** 🎉\n\n"
                f"📋 رقم الطلب: `{order_number}`\n"
                f"📦 المنتج: {product['name']}\n"
                f"💰 المبلغ: {Config.CURRENCY_SYMBOL}{product['price']:.2f}\n"
                f"💵 الرصيد المتبقي: {Config.CURRENCY_SYMBOL}{user['balance'] - product['price']:.2f}\n\n"
                f"📝 **تفاصيل المنتج:**\n{details}\n\n"
                f"📌 تم حفظ المنتج في سجل مشترياتك.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # إشعار للإدارة
            for admin_id in Config.ADMIN_IDS:
                try:
                    await query.bot.send_message(
                        chat_id=admin_id,
                        text=f"🛒 **عملية شراء جديدة**\n\n"
                             f"👤 المستخدم: {user['first_name']} (@{user['username']})\n"
                             f"📦 المنتج: {product['name']}\n"
                             f"💰 المبلغ: {Config.CURRENCY_SYMBOL}{product['price']:.2f}\n"
                             f"📋 الطلب: {order_number}"
                    )
                except:
                    pass
        
        except Exception as e:
            self.db.unfreeze_balance(user['id'], product['price'])
            await query.edit_message_text(f"❌ حدث خطأ أثناء الشراء: {str(e)}")
    
    async def show_balance(self, query):
        """عرض الرصيد"""
        user_id = query.from_user.id
        user = self.db.get_user(email=f"{user_id}@telegram.com")
        
        if not user:
            await query.edit_message_text("⚠️ يرجى استخدام /start أولاً")
            return
        
        text = f"""
💰 **الرصيد الحالي**

👤 المستخدم: {user['first_name']}
💵 الرصيد: {Config.CURRENCY_SYMBOL}{user['balance']:.2f}
🔒 الرصيد المجمد: {Config.CURRENCY_SYMBOL}{user['frozen_balance']:.2f}
💎 مستوى VIP: {Config.VIP_LEVELS[user['vip_level']]['name']}
💰 إجمالي المشتريات: {Config.CURRENCY_SYMBOL}{user['total_spent']:.2f}
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 سجل المعاملات", callback_data="transactions")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")],
        ]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_orders(self, query):
        """عرض الطلبات"""
        user_id = query.from_user.id
        user = self.db.get_user(email=f"{user_id}@telegram.com")
        
        if not user:
            await query.edit_message_text("⚠️ يرجى استخدام /start أولاً")
            return
        
        orders = self.db.get_user_orders(user['id'])
        
        if not orders:
            await query.edit_message_text("📦 لا توجد طلبات حتى الآن")
            return
        
        text = "📦 **سجل المشتريات**\n\n"
        
        for order in orders[:5]:
            status_emoji = {
                'pending': '⏳',
                'processing': '🔄',
                'completed': '✅',
                'cancelled': '❌',
                'refunded': '🔄'
            }.get(order['status'], '❓')
            
            text += f"{status_emoji} **طلب #{order['order_number']}**\n"
            text += f"💰 المبلغ: {Config.CURRENCY_SYMBOL}{order['total_amount']:.2f}\n"
            text += f"📅 التاريخ: {order['created_at'][:16]}\n"
            text += f"📌 الحالة: {order['status']}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")],
        ]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_profile(self, query):
        """عرض الملف الشخصي"""
        user_id = query.from_user.id
        user = self.db.get_user(email=f"{user_id}@telegram.com")
        
        if not user:
            await query.edit_message_text("⚠️ يرجى استخدام /start أولاً")
            return
        
        vip_level = Config.VIP_LEVELS[user['vip_level']]
        
        text = f"""
👤 **الملف الشخصي**

🆔 المعرف: {user['id']}
👤 الاسم: {user['first_name']} {user['last_name'] or ''}
📝 البريد الإلكتروني: {user['email']}

💎 مستوى VIP: {vip_level['name']}
🎁 خصم VIP: {vip_level['discount']}%
💰 الرصيد: {Config.CURRENCY_SYMBOL}{user['balance']:.2f}
💸 إجمالي المشتريات: {Config.CURRENCY_SYMBOL}{user['total_spent']:.2f}
⭐ عدد الإحالات: {user['referral_count']}

🔹 **رابط الإحالة:**
https://t.me/{query.message.chat.username}?start={user['referral_code']}
        """
        
        keyboard = [
            [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")],
        ]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_transactions(self, query):
        """عرض المعاملات"""
        user_id = query.from_user.id
        user = self.db.get_user(email=f"{user_id}@telegram.com")
        
        if not user:
            await query.edit_message_text("⚠️ يرجى استخدام /start أولاً")
            return
        
        transactions = self.db.get_transactions(user['id'], limit=10)
        
        if not transactions:
            await query.edit_message_text("📊 لا توجد معاملات حتى الآن")
            return
        
        text = "📊 **سجل المعاملات المالية**\n\n"
        
        for tx in transactions:
            amount_sign = "+" if tx['amount'] > 0 else ""
            status_emoji = {
                'pending': '⏳',
                'completed': '✅',
                'failed': '❌'
            }.get(tx['status'], '❓')
            
            text += f"{status_emoji} {tx['type']}: {amount_sign}{Config.CURRENCY_SYMBOL}{abs(tx['amount']):.2f}\n"
            text += f"📅 {tx['created_at'][:16]}\n"
            text += f"📝 {tx['description'][:40]}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🔙 رجوع", callback_data="balance")],
        ]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def admin_stats(self, query):
        """إحصائيات الإدارة"""
        stats = self.db.get_stats('daily')
        weekly = self.db.get_stats('weekly')
        monthly = self.db.get_stats('monthly')
        
        total_users = len(self.db.get_users(limit=999999))
        total_products = len(self.db.get_products(limit=999999))
        total_orders = self.db.execute_query("SELECT COUNT(*) FROM orders", fetch_one=True)[0] or 0
        
        text = f"""
📊 **إحصائيات النظام**

👥 **المستخدمين:**
• إجمالي: {total_users}
• اليوم: {stats['users']}
• الأسبوع: {weekly['users']}
• الشهر: {monthly['users']}

📦 **المنتجات:**
• إجمالي: {total_products}

📋 **الطلبات:**
• إجمالي: {total_orders}
• اليوم: {stats['orders']}
• الأسبوع: {weekly['orders']}
• الشهر: {monthly['orders']}

💰 **الإيرادات:**
• اليوم: {Config.CURRENCY_SYMBOL}{stats['revenue']:.2f}
• الأسبوع: {Config.CURRENCY_SYMBOL}{weekly['revenue']:.2f}
• الشهر: {Config.CURRENCY_SYMBOL}{monthly['revenue']:.2f}
        """
        
        keyboard = [
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")],
        ]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def admin_products(self, query):
        """إدارة المنتجات"""
        text = """
📦 **إدارة المنتجات**

🔹 **الإجراءات المتاحة:**
• /add_product - إضافة منتج
• /edit_product [id] - تعديل منتج
• /delete_product [id] - حذف منتج
• /add_category - إضافة قسم
• /edit_category [id] - تعديل قسم
• /delete_category [id] - حذف قسم
        """
        
        keyboard = [
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")],
        ]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def admin_users(self, query):
        """إدارة المستخدمين"""
        text = """
👤 **إدارة المستخدمين**

🔹 **الإجراءات المتاحة:**
• /list_users - عرض المستخدمين
• /user_info [id] - معلومات مستخدم
• /block_user [id] - حظر مستخدم
• /unblock_user [id] - فك الحظر
• /add_balance [id] [amount] - إضافة رصيد
• /remove_balance [id] [amount] - خصم رصيد
        """
        
        keyboard = [
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")],
        ]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def admin_orders(self, query):
        """إدارة الطلبات"""
        text = """
📋 **إدارة الطلبات**

🔹 **الإجراءات المتاحة:**
• /list_orders - عرض الطلبات
• /order_info [id] - معلومات طلب
• /update_order [id] [status] - تحديث حالة
• /cancel_order [id] - إلغاء طلب
        """
        
        keyboard = [
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")],
        ]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def admin_broadcast(self, query):
        """الإذاعة"""
        await query.edit_message_text(
            "📢 **الإذاعة**\n\n"
            "أرسل رسالتك للإذاعة:\n"
            "/broadcast رسالتك هنا\n\n"
            "مثال: /broadcast عروض جديدة في المتجر! 🎉",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الرسائل النصية"""
        message = update.message.text
        
        # معالجة أوامر الإذاعة
        if message.startswith('/broadcast'):
            if update.effective_user.id not in Config.ADMIN_IDS:
                await update.message.reply_text("⛔ غير مصرح لك")
                return
            
            broadcast_message = message.replace('/broadcast', '').strip()
            if not broadcast_message:
                await update.message.reply_text("❌ يرجى كتابة رسالة للإذاعة")
                return
            
            # إرسال الإذاعة
            users = db.execute_query(
                "SELECT * FROM users",
                fetch_all=True
            )
            
            sent = 0
            for user in users:
                try:
                    await update.bot.send_message(
                        chat_id=user[1],  # telegram_id
                        text=f"📢 **إذاعة من الإدارة**\n\n{broadcast_message}",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    sent += 1
                except:
                    pass
            
            await update.message.reply_text(
                f"✅ تم إرسال الإذاعة\n"
                f"📨 تم الإرسال: {sent}"
            )
    
    def generate_password(self):
        """توليد كلمة مرور عشوائية"""
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choices(chars, k=12))
    
    async def run(self):
        """تشغيل البوت"""
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=logging.INFO
        )
        
        await self.application.initialize()
        await self.application.start()
        
        if Config.BOT_WEBHOOK_URL:
            # وضع Webhook
            await self.application.bot.set_webhook(
                f"{Config.BOT_WEBHOOK_URL}{Config.BOT_WEBHOOK_PATH}"
            )
            print(f"✅ البوت يعمل على Webhook: {Config.BOT_WEBHOOK_URL}")
        else:
            # وضع Polling
            await self.application.updater.start_polling()
            print("✅ البوت يعمل على وضع Polling")
        
        print(f"🤖 {Config.APP_NAME} - البوت يعمل الآن!")
        
        await asyncio.Event().wait()

# ==================== وظيفة التشغيل الرئيسية ====================

def run_web_app():
    """تشغيل تطبيق الويب"""
    app.run(host='0.0.0.0', port=5000, debug=Config.DEBUG)

def run_bot():
    """تشغيل البوت"""
    bot = TelegramBot()
    asyncio.run(bot.run())

async def run_bot_async():
    """تشغيل البوت بشكل غير متزامن"""
    bot = TelegramBot()
    await bot.run()

def main():
    """الوظيفة الرئيسية"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Digital Shop Platform')
    parser.add_argument('--web', action='store_true', help='تشغيل تطبيق الويب فقط')
    parser.add_argument('--bot', action='store_true', help='تشغيل البوت فقط')
    parser.add_argument('--all', action='store_true', help='تشغيل الكل')
    
    args = parser.parse_args()
    
    if args.web:
        run_web_app()
    elif args.bot:
        run_bot()
    elif args.all:
        # تشغيل الكل في خيوط منفصلة
        import threading
        
        web_thread = threading.Thread(target=run_web_app)
        bot_thread = threading.Thread(target=run_bot)
        
        web_thread.start()
        bot_thread.start()
        
        web_thread.join()
        bot_thread.join()
    else:
        # تشغيل الكل افتراضيًا
        import threading
        
        web_thread = threading.Thread(target=run_web_app)
        bot_thread = threading.Thread(target=run_bot)
        
        web_thread.start()
        bot_thread.start()
        
        web_thread.join()
        bot_thread.join()

if __name__ == "__main__":
    main()