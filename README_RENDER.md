# Despliegue en Render con Cloudinary

Este proyecto ya quedo preparado para:

- desplegarse en Render como **Web Service**,
- usar **Cloudinary** para almacenar las imagenes subidas,
- seguir usando **WhiteNoise** para archivos estaticos,
- evitar perder imagenes en produccion por el filesystem efimero de Render.

## Variables que debes configurar en Render

En tu servicio web agrega estas variables:

- `SECRET_KEY`
- `DEBUG=False`
- `USE_CLOUDINARY=True`
- `ALLOWED_HOSTS=tu-app.onrender.com`
- `CSRF_TRUSTED_ORIGINS=https://tu-app.onrender.com`
- `DATABASE_URL=...`
- `CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name>`

## Flujo recomendado

1. Sube el proyecto a GitHub.
2. En Render crea un **Web Service** apuntando a tu repositorio.
3. Usa el archivo `render.yaml` o configura manualmente:
   - Build Command: `./build.sh`
   - Start Command: `gunicorn platans_validacion.wsgi:application`
4. Crea o conecta una base de datos PostgreSQL y pega su `DATABASE_URL`.
5. Agrega tu `CLOUDINARY_URL`.
6. Haz deploy.
7. En Render Shell ejecuta `python manage.py createsuperuser` si aun no tienes usuario administrador.

## Desarrollo local

- Si no defines `DATABASE_URL`, el proyecto cae automaticamente a `sqlite3`.
- Si no defines `USE_CLOUDINARY=True`, el proyecto usa almacenamiento local en `media/`.
- Si quieres probar Cloudinary localmente, define `USE_CLOUDINARY=True` y `CLOUDINARY_URL`.

## Migrar imagenes existentes desde media/ a Cloudinary

Si ya tienes imagenes locales cargadas en `media/imagenes_validacion`, no se suben solas a Cloudinary.

Con tus credenciales activas, ejecuta localmente:

```bash
export USE_CLOUDINARY=True
export CLOUDINARY_URL='cloudinary://<api_key>:<api_secret>@<cloud_name>'
python manage.py sync_images_to_cloudinary
```

Si tu carpeta media esta en otra ruta:

```bash
python manage.py sync_images_to_cloudinary --media-root /ruta/a/media
```

## Notas importantes

- No subas `.env` a GitHub.
- No subas `media/` ni `staticfiles/` al repositorio.
- El script `scripts/ensure_jazzmin_sourcemaps.py` evita un fallo de `collectstatic` causado por sourcemaps faltantes de Jazzmin.
- Si ya expusiste tu `API Secret`, regeneralo en Cloudinary antes de publicar el repositorio.
