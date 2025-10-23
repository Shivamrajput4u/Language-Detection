# Language-Detection
# OCR Language Detection API 📝

This project is a Django-based web application that performs Optical Character Recognition (OCR) on an uploaded image to extract text and then detects the language of that extracted text. It leverages the Ultralytics YOLO model for robust text detection and the `langdetect` library for language identification.



---

## ✨ Features

* **Image Upload**: Simple interface to upload image files (`.jpg`, `.png`, etc.).
* **Text Extraction**: Utilizes a powerful OCR engine to accurately extract text from the provided image.
* **Language Identification**: Automatically detects the language of the extracted text.
* **RESTful API**: Provides a clean API endpoint for programmatic access and integration.

---

## 🛠️ Tech Stack

* **Backend**: Django
* **Machine Learning / OCR**: PyTorch, Ultralytics (YOLO), OpenCV
* **Language Detection**: langdetect
* **Image Processing**: Pillow
* **Numerical Operations**: NumPy

---

## 🚀 Getting Started

Follow these instructions to get a copy of the project up and running on your local machine for development and testing.

### Prerequisites

* Python 3.10+
* `pip` package manager
* `git` for cloning the repository

### ⚙️ Installation

1.  **Clone the repository:**
    ```shell
    git clone [https://github.com/your-username/Language-Detection.git](https://github.com/your-username/Language-Detection.git)
    cd Language-Detection
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```shell
    python3 -m venv venv
    source venv/bin/activate
    ```
    *On Windows, use `venv\Scripts\activate`*

3.  **Install required system dependencies:**
    OpenCV requires certain graphics libraries to function correctly. Install them using your system's package manager.
    ```shell
    # For Debian/Ubuntu-based systems
    sudo apt-get update && sudo apt-get install -y libgl1
    ```

4.  **Install Python packages:**
    All required Python libraries are listed in the `requirements.txt` file.
    ```shell
    pip install -r requirements.txt
    ```

5.  **Apply Django database migrations:**
    ```shell
    python manage.py migrate
    ```

### ▶️ Running the Application

1.  **Start the Django development server:**
    ```shell
    python manage.py runserver 0.0.0.0:8000
    ```
    This will run the server on your local network at port 8000.

2.  **Access the application:**
    Open your web browser and navigate to `http://127.0.0.1:8000` to use the web interface.

---

## 🔌 API Usage

The application exposes an API endpoint for detecting language from an image.

### Endpoint: `/api/detect/`

* **Method**: `POST`
* **Content-Type**: `multipart/form-data`
* **Body**: Requires an `image` file.

#### Example Request (`curl`)

```shell
curl -X POST -F "image=@/path/to/your/image.jpg" [http://127.0.0.1:8000/api/detect/](http://127.0.0.1:8000/api/detect/)
```

#### ✅ Success Response (200 OK)

```json
{
  "detected_text": "This is a sample text in English.",
  "language_code": "en",
  "language_name": "English"
}
```

#### ❌ Error Response (400 Bad Request)

```json
{
  "error": "No image file provided."
}
```

---

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.
