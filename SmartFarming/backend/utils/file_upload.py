"""
File Upload Utility - Cloudinary Integration for Product Images and User Avatars
"""

import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

class FileUploadService:
    """Handle file uploads to Cloudinary"""
    
    @staticmethod
    def allowed_file(filename):
        """Check if file extension is allowed"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    @staticmethod
    def upload_product_image(file, product_id):
        """Upload product image"""
        try:
            if not FileUploadService.allowed_file(file.filename):
                return {'error': 'File type not allowed'}, 400
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file,
                folder=f'smart_farming/products/{product_id}',
                resource_type='auto',
                transformation=[
                    {'width': 800, 'height': 600, 'crop': 'fill', 'quality': 'auto'},
                    {'fetch_format': 'auto'}
                ]
            )
            
            return {
                'url': result['secure_url'],
                'public_id': result['public_id'],
                'size': result['bytes']
            }, 200
        
        except Exception as e:
            print(f"Upload product image error: {e}")
            return {'error': str(e)}, 500
    
    @staticmethod
    def upload_profile_picture(file, user_id, user_type):
        """Upload user profile picture"""
        try:
            if not FileUploadService.allowed_file(file.filename):
                return {'error': 'File type not allowed'}, 400
            
            result = cloudinary.uploader.upload(
                file,
                folder=f'smart_farming/{user_type}/{user_id}',
                resource_type='auto',
                public_id=f'profile_{user_id}',
                overwrite=True,
                transformation=[
                    {'width': 500, 'height': 500, 'crop': 'fill', 'gravity': 'face', 'quality': 'auto'},
                    {'fetch_format': 'auto'}
                ]
            )
            
            return {
                'url': result['secure_url'],
                'public_id': result['public_id']
            }, 200
        
        except Exception as e:
            print(f"Upload profile picture error: {e}")
            return {'error': str(e)}, 500
    
    @staticmethod
    def upload_multiple_images(files, product_id):
        """Upload multiple product images"""
        try:
            uploaded = []
            
            for file in files:
                if not FileUploadService.allowed_file(file.filename):
                    continue
                
                result = cloudinary.uploader.upload(
                    file,
                    folder=f'smart_farming/products/{product_id}',
                    resource_type='auto',
                    transformation=[
                        {'width': 800, 'height': 600, 'crop': 'fill', 'quality': 'auto'},
                        {'fetch_format': 'auto'}
                    ]
                )
                
                uploaded.append({
                    'url': result['secure_url'],
                    'public_id': result['public_id']
                })
            
            return {'images': uploaded}, 200
        
        except Exception as e:
            print(f"Upload multiple images error: {e}")
            return {'error': str(e)}, 500
    
    @staticmethod
    def delete_image(public_id):
        """Delete image from Cloudinary"""
        try:
            cloudinary.uploader.destroy(public_id)
            return {'message': 'Image deleted successfully'}, 200
        
        except Exception as e:
            print(f"Delete image error: {e}")
            return {'error': str(e)}, 500
    
    @staticmethod
    def get_transformation_url(public_id, width=400, height=400, crop='fill'):
        """Get transformed image URL"""
        try:
            url = cloudinary.CloudinaryResource(public_id=public_id).build_url(
                width=width,
                height=height,
                crop=crop,
                quality='auto',
                fetch_format='auto'
            )
            return url
        
        except Exception as e:
            print(f"Get transformation URL error: {e}")
            return None
