
import os

import cloudinary.uploader
from cloudinary_storage.storage import MediaCloudinaryStorage


class CloudinaryDocumentStorage(MediaCloudinaryStorage):
    """
    Almacena documentos como recursos raw en Cloudinary.
    """

    def _get_resource_type(self, name):
        return "raw"

    def _upload(self, name, content):
        options = {
            "resource_type": "raw",
            "use_filename": True,
            "tags": self.TAG,
        }

        folder = os.path.dirname(name)
        if folder:
            options["folder"] = folder

        return cloudinary.uploader.upload(
            content,
            **options,
        )
