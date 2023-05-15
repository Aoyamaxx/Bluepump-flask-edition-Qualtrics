import os
import sys

def rename_images_and_generate_code():
    folder_path = input("Enter the folder path: ")
    country_name = input("Enter the country name: ")

    if not os.path.exists(folder_path):
        print("Folder not found!")
        sys.exit(1)

    filenames = os.listdir(folder_path)
    image_filenames = [f for f in filenames if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]

    renamed_images = []
    for i, filename in enumerate(image_filenames, start=1):
        new_name = f"{country_name}{i}.jpg"
        os.rename(os.path.join(folder_path, filename), os.path.join(folder_path, new_name))
        renamed_images.append({'filename': f'{country_name}/{new_name}'})

    code = f"""
@app.route('/gallery_{country_name}')
def gallery_{country_name}():
    country_images = {renamed_images}
    return render_template('gallery_{country_name}.html', country_images=country_images)
"""

    output_path = os.path.join(folder_path, f'{country_name}_code.txt')
    with open(output_path, 'w') as f:
        f.write(code.strip())

    print(f"Code generated in {output_path}")

if __name__ == '__main__':
    rename_images_and_generate_code()