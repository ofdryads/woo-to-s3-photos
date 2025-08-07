# woo-to-s3-photos
Migrate photos from WooCommerce/WordPress to an AWS S3 bucket to migrate your website off of WordPress, or to have better performance on your current website
- Download all the product photos for your entire product catalog
- Convert older/larger image formats to .webp
- Upload to an S3 bucket

# Instructions
The value for wc_csv is the path to a file that you export from WooCommerce. Under Products -> Export, check "ID", "Name", "Published", and "Images", then click "Generate CSV", and this file will download.
