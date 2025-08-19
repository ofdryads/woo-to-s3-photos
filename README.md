# Woo-to-S3 Product Photos
Convert product photos on a WooCommerce/WordPress site to .webp in bulk and migrate them to an AWS S3 bucket. Good for migrating off of WooCommerce and onto another platform, or for saving storage/improving performance on an existing website.

- Downloads all the product photos for your entire product catalog 
- Converts older/larger image formats to .webp
- Uploads the resulting .webp product photos to an S3 bucket, with the photos organized in folders by product

## Instructions
The value for wc_csv is the path to a file that you export from WooCommerce. Under Products -> Export, check "ID", "Name", "Published", and "Images", then click "Generate CSV", and this file will download.

Descriptions for required config variables are in .env.example

Run migrate-photos.py


