# Woo-to-S3 Product Photos
Convert photos from WooCommerce/WordPress to .webp and migrate them to an AWS S3 bucket. This can help you migrate your eCommerce website off of WordPress and onto another platform, or improve performance on your current website.
- Download all the product photos for your entire product catalog, organizing them in folders by product name
- Convert images with older/larger formats to .webp
- Upload the .webp images to an S3 bucket in product subfolders and each with a product name metadata tag 

## Instructions
The value for wc_csv is the path to a file that you export from WooCommerce. Under Products -> Export, check "ID", "Name", "Published", and "Images", then click "Generate CSV", and this file will download.

Descriptions for required config variables are in .env.example

Run migrate-photos.py


