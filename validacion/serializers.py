import base64
from rest_framework import serializers
from .models import ImagenValidacion

MAX_IMAGE_SIZE_MB = 10
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024


class ImagenValidacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagenValidacion
        fields = "__all__"
        read_only_fields = ("subida_por", "fecha_subida", "imagen_base64")

    def validate_imagen(self, value):
        content_type = getattr(value, "content_type", "")
        if content_type and not content_type.startswith("image/"):
            raise serializers.ValidationError(
                "El archivo enviado debe ser una imagen válida."
            )

        if value.size > MAX_IMAGE_SIZE_BYTES:
            raise serializers.ValidationError(
                f"Cada imagen debe pesar como máximo {MAX_IMAGE_SIZE_MB} MB."
            )

        value.seek(0)
        return value

    def create(self, validated_data):
        imagen_file = validated_data.get("imagen")
        seleccionada = validated_data.get("seleccionada", False)

        if imagen_file and seleccionada:
            imagen_file.seek(0)
            validated_data["imagen_base64"] = base64.b64encode(
                imagen_file.read()
            ).decode("utf-8")
            imagen_file.seek(0)

        return super().create(validated_data)
