"""
Django settings for webapps project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import ConfigParser
import os
# BASE_DIR = os.path.dirname(os.path.dirname(__file__))

config = ConfigParser.ConfigParser()
config.read("config.ini")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'k&xuencjt-bdv8gy7qp*^-u4di2cl$apuv1&s#eiec_=mv7i)h'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',

    # Required by `allauth` template tags
    'django.core.context_processors.request',

    # `allauth` specific context processors
    'allauth.account.context_processors.account',
    'allauth.socialaccount.context_processors.socialaccount',
    'django.contrib.messages.context_processors.messages',

)

AUTHENTICATION_BACKENDS = (

    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',

)
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # 'haystack',
    'dreamrise',
    "django_forms_bootstrap",
    "payments",
    #new feature for social auth
    # The Django sites framework is required
    'django.contrib.sites',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # ... include the providers you want to enable:
    # 'allauth.socialaccount.providers.amazon',
    # 'allauth.socialaccount.providers.angellist',
    # 'allauth.socialaccount.providers.bitbucket',
    # 'allauth.socialaccount.providers.bitly',
    # 'allauth.socialaccount.providers.coinbase',
    # 'allauth.socialaccount.providers.dropbox',
    # # 'allauth.socialaccount.providers.dropbox_oauth2',
    # 'allauth.socialaccount.providers.evernote',
    'allauth.socialaccount.providers.facebook',
    # 'allauth.socialaccount.providers.flickr',
    # 'allauth.socialaccount.providers.feedly',
    # 'allauth.socialaccount.providers.fxa',
    # 'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.google',
    # 'allauth.socialaccount.providers.hubic',
    # 'allauth.socialaccount.providers.instagram',
    # 'allauth.socialaccount.providers.linkedin',
    # 'allauth.socialaccount.providers.linkedin_oauth2',
    # 'allauth.socialaccount.providers.odnoklassniki',
    # 'allauth.socialaccount.providers.openid',
    # 'allauth.socialaccount.providers.persona',
    # 'allauth.socialaccount.providers.soundcloud',
    # 'allauth.socialaccount.providers.spotify',
    # 'allauth.socialaccount.providers.stackexchange',
    # 'allauth.socialaccount.providers.tumblr',
    # 'allauth.socialaccount.providers.twitch',
    # 'allauth.socialaccount.providers.twitter',
    # 'allauth.socialaccount.providers.vimeo',
    # 'allauth.socialaccount.providers.vk',
    # 'allauth.socialaccount.providers.weibo',
    # 'allauth.socialaccount.providers.xing',
)
SITE_ID = 1

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'django.contrib.sessions.middleware.SessionMiddleware',
    # 'django.contrib.messages.middleware.MessageMiddleware',
    # 'payments.middleware.ActiveSubscriptionMiddleware',
)

ROOT_URLCONF = 'webapps.urls'

WSGI_APPLICATION = 'webapps.wsgi.application'

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
        #'URL': 'http://localhost:8983/solr',
        #'URL': 'http://127.0.0.1:3072/solr'
        #'URL': 'http://127.0.0.1:8983/solr'
        # ...or for multicore...
        # 'URL': 'http://127.0.0.1:8983/solr/mysite',
    },
}

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.postgresql_psycopg2',
    #     'NAME': config.get('Database', 'Name'),
    #     'USER': config.get('Database', 'User'),
    #     'PASSWORD': config.get('Database', 'Password')
    # }
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('Database_Name'),
        'USER': os.environ.get('Database_User'),
        'PASSWORD': os.environ.get('Database_Password')
    }
    # 'default': {
    #     'ENGINE': 'django.db.backends.postgresql_psycopg2',
    #     'NAME': os.environ.get('Database_Name'),
    #     'USER': os.environ.get('Database_User'),
    #     'PASSWORD': os.environ.get('Database_Password')
    # }
}

LOGIN_URL = '/dreamrise/login'

LOGIN_REDIRECT_URL = '/dreamrise/'

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'US/Eastern'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

# STATIC_URL = '/dreamrise/static/dreamrise/'
MEDIA_URL = '/picture/'

# Additional locations of static files
# STATICFILES_DIRS = [os.path.join(BASE_DIR, 'dreamrise/static/dreamrise')]




# STRIPE_PUBLIC_KEY = config.get('Stripe', 'STRIPE_PUBLIC_KEY')
# STRIPE_SECRET_KEY = config.get('Stripe', 'STRIPE_SECRET_KEY')

STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')

config = ConfigParser.ConfigParser()
config.read("config.ini")

# EMAIL_HOST = os.environ.get('Email_Host')
# EMAIL_PORT = os.environ.get('Email_Port')
# EMAIL_HOST_USER = os.environ.get('Email_User')
# EMAIL_HOST_PASSWORD = os.environ.get('Email_Password')
EMAIL_HOST = os.environ.get('Email_Host')
EMAIL_PORT = os.environ.get('Email_Port')
EMAIL_HOST_USER = os.environ.get('Email_User')
EMAIL_HOST_PASSWORD = os.environ.get('Email_Password')
EMAIL_USE_SSL = True

# Parse database configuration from $DATABASE_URL
import dj_database_url
DATABASES['default'] =  dj_database_url.config()

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Allow all host headers
ALLOWED_HOSTS = ['*']

# Static asset configuration
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = 'staticfiles'
STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)