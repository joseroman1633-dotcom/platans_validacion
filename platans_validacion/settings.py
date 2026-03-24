import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def env_list(name: str, default: list[str] | None = None) -> list[str]:
    value = os.getenv(name, "")
    if value:
        return [item.strip() for item in value.split(",") if item.strip()]
    return list(default or [])


RENDER = env_bool("RENDER", False)
DEBUG = env_bool("DEBUG", not RENDER)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-local-change-me")

ALLOWED_HOSTS = set(env_list("ALLOWED_HOSTS", ["127.0.0.1", "localhost"]))
render_external_hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if render_external_hostname:
    ALLOWED_HOSTS.add(render_external_hostname)
ALLOWED_HOSTS = sorted(ALLOWED_HOSTS)

CSRF_TRUSTED_ORIGINS = set(env_list("CSRF_TRUSTED_ORIGINS"))
render_external_url = os.getenv("RENDER_EXTERNAL_URL")
if render_external_url:
    CSRF_TRUSTED_ORIGINS.add(render_external_url)
CSRF_TRUSTED_ORIGINS = sorted(CSRF_TRUSTED_ORIGINS)

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "cloudinary_storage",
    "cloudinary",
    "rest_framework",
    "inicio",
    "validacion",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "platans_validacion.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "platans_validacion.wsgi.application"

local_database_url = os.getenv(
    "LOCAL_DATABASE_URL",
    f"sqlite:///{(BASE_DIR / 'db.sqlite3').as_posix()}",
)

DATABASES = {
    "default": dj_database_url.config(
        default=local_database_url,
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=RENDER,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

USE_CLOUDINARY = env_bool("USE_CLOUDINARY", RENDER)

cloudinary_url = os.getenv("CLOUDINARY_URL", "").strip()
cloudinary_cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
cloudinary_api_key = os.getenv("CLOUDINARY_API_KEY", "").strip()
cloudinary_api_secret = os.getenv("CLOUDINARY_API_SECRET", "").strip()

if cloudinary_url:
    if not cloudinary_url.startswith("cloudinary://"):
        raise ImproperlyConfigured(
            "CLOUDINARY_URL debe iniciar con 'cloudinary://'"
        )
    try:
        parsed = cloudinary_url.replace("cloudinary://", "", 1)
        creds, cloud_name = parsed.split("@", 1)
        api_key, api_secret = creds.split(":", 1)
        cloudinary_cloud_name = cloud_name.strip()
        cloudinary_api_key = api_key.strip()
        cloudinary_api_secret = api_secret.strip()
    except ValueError as exc:
        raise ImproperlyConfigured(
            "CLOUDINARY_URL no tiene el formato correcto. "
            "Usa: cloudinary://API_KEY:API_SECRET@CLOUD_NAME"
        ) from exc

cloudinary_is_configured = bool(
    cloudinary_cloud_name and cloudinary_api_key and cloudinary_api_secret
)

MEDIA_URL = "/media/"

if USE_CLOUDINARY and not cloudinary_is_configured:
    raise ImproperlyConfigured(
        "USE_CLOUDINARY esta activo, pero faltan credenciales de Cloudinary. "
        "Define CLOUDINARY_URL o CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY y CLOUDINARY_API_SECRET."
    )

if USE_CLOUDINARY:
    CLOUDINARY_STORAGE = {
        "CLOUD_NAME": cloudinary_cloud_name,
        "API_KEY": cloudinary_api_key,
        "API_SECRET": cloudinary_api_secret,
        "SECURE": True,
    }

    CLOUDINARY = {
        "cloud_name": cloudinary_cloud_name,
        "api_key": cloudinary_api_key,
        "api_secret": cloudinary_api_secret,
        "secure": True,
    }

    default_storage_backend = "cloudinary_storage.storage.MediaCloudinaryStorage"
else:
    MEDIA_ROOT = BASE_DIR / "media"
    default_storage_backend = "django.core.files.storage.FileSystemStorage"

STORAGES = {
    "default": {
        "BACKEND": default_storage_backend,
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        if DEBUG
        else "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/home2/"
LOGOUT_REDIRECT_URL = "/"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ]
}

JAZZMIN_SETTINGS = {
    "site_title": "Platans Validacion System",
    "site_header": "Platans Validacion System",
    "site_brand": "Platans Validacion System",
    "welcome_sign": "Bienvenido al panel de administración",
    "copyright": "Platans",
    "search_model": [],
    "topmenu_links": [
        {"name": "Inicio", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Gráficas internas", "url": "admin_graficas", "permissions": ["auth.view_user"]},
        {"name": "Gráficas públicas", "url": "admin_graficas_publicas", "permissions": ["auth.view_user"]},
        {"name": "Cerrar sesión", "url": "salir", "permissions": ["auth.view_user"]},
    ],
    "custom_links": {
        "validacion": [
            {
                "name": "Gráficas internas",
                "url": "admin_graficas",
                "icon": "fas fa-chart-bar",
                "permissions": ["auth.view_user"],
            },
            {
                "name": "Gráficas públicas",
                "url": "admin_graficas_publicas",
                "icon": "fas fa-chart-pie",
                "permissions": ["auth.view_user"],
            },
        ],
    },
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "inicio.PerfilUsuario": "fas fa-id-card",
        "validacion.ImagenValidacion": "fas fa-image",
        "validacion.PruebaImagenRespuesta": "fas fa-check-circle",
        "validacion.SesionPrueba": "fas fa-list",
    },
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": [
        "inicio",
        "validacion",
        "auth",
    ],
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", not DEBUG)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_HSTS_SECONDS = 3600 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
