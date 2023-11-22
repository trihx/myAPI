import requests

# Đường dẫn đến API của bạn
api_url = 'http://localhost:5000/predict_sentiment'  # Thay đổi URL này nếu cần

# Dữ liệu đầu vào cho dự đoán
data = {
    "reviews": ["ngon","dở","tệ"]
}

# Gửi yêu cầu POST đến API
response = requests.post(api_url, json=data)

# Kiểm tra xem yêu cầu đã thành công không (status code 200)
if response.status_code == 200:
    results = response.json()  # Lấy kết quả dự đoán từ phản hồi JSON
    for result in results:
        print(f"Review: '{result['review']}' - Predicted Sentiment: {result['predicted_sentiment']}")
else:
    print("Failed to make a request to the API.")
