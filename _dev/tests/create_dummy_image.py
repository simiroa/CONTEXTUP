from PIL import Image, ImageDraw

def create_test_image(path):
    img = Image.new('RGB', (512, 512), color='red')
    d = ImageDraw.Draw(img)
    d.rectangle([128, 128, 384, 384], fill='blue')
    img.save(path)
    print(f"Created {path}")

if __name__ == "__main__":
    create_test_image("tests/test_image.jpg")
