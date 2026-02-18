from backend.app.services.image_preprocessing import preprocess_image

TEST_IMAGE_PATH = r"C:\Users\kunle\OneDrive\Documents\PetGuardAI_MVP\test_images\dog.jpg"

tensor = preprocess_image(TEST_IMAGE_PATH)

print("✅ Preprocessing successful")
print("Tensor shape:", tensor.shape)
print("Tensor dtype:", tensor.dtype)
print("Min pixel value:", tensor.numpy().min())
print("Max pixel value:", tensor.numpy().max())
