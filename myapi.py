from selenium import webdriver
from time import sleep
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException

from flask import Flask, request, render_template, jsonify
import joblib
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from keras.models import load_model
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from tensorflow import keras




app = Flask(__name__)

# Load mô hình và CountVectorizer
loaded_model = joblib.load('multinomial_nb_model.joblib')
cv = joblib.load('count_vectorizer3.joblib')

# Load mô hình Logistic Regression
loaded_model_logistic = joblib.load('logistic_regression_model.joblib')

# Load mô hình LSTM và tokenizer
lstm_model = keras.models.load_model('lstm_model.h5')
# Load tokenizer
with open('tokenizer.pickle', 'rb') as handle:
    tokenizer = joblib.load(handle)


@app.route('/')
def home():
    return render_template('index.html')
    
@app.route('/load_more_comments', methods=['POST'])
def load_more_comments():
    start = int(request.form['start'])
    end = int(request.form['end'])
    # Trích xuất bình luận từ start đến end từ danh sách bình luận đầy đủ
    comments_to_load = all_comments[start:end]
    return render_template('comment_table.html', comments=comments_to_load)

@app.route('/get_comments', methods=['POST'])
def get_comments():
    url = request.form['url']  # Đường dẫn bạn muốn lấy bình luận

    comment_list = []

    # 1. Khai báo browser
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

    # 2. Mở URL của post
    driver.get(url)
    sleep(random.randint(5, 10))

    review_count = driver.find_element(
    "xpath", "/html/body/div[2]/div[2]/div[2]/section/div/div/div/div/div[1]/div/div/div[1]/div/div[1]/div/ul/li[1]/a/span")

    review_count = int(review_count.text)
    print(f"Có {review_count} bình luận.")

    for i in range(review_count):
        print(f"Crawl bình luận thứ {i}")
        try:
            if i % 10 == 0:
                showcomment_link = driver.find_element(
                    "xpath", "/html/body/div[2]/div[2]/div[2]/section/div/div/div/div/div[1]/div/div/div[1]/div/div[2]/a")
                showcomment_link.click()
                sleep(random.randint(5, 10))
        except NoSuchElementException:
            print("No Such Element Exception!" + str(i))
        li_elements = driver.find_elements(
            "xpath", f"/html/body/div[2]/div[2]/div[2]/section/div/div/div/div/div[1]/div/div/div[1]/div/ul/li[{i}]/div[2]/div")

        for li in li_elements:
            txt = li.text.replace("Xem thêm", "").replace("\n", "")
            comment_list.append(txt)

    with open('comments.txt', 'w', encoding='utf-8') as file:
        for comment in comment_list:
            comment = comment.replace('\n', ' ')
            file.write(comment + '\n')
    driver.close()

    print(comment_list)

    return multipredict()


@app.route('/predict', methods=['POST'])
def predict():
    review = request.form['review']
    reviews_to_predict = [review]

    # Chuyển đổi đánh giá mẫu thành dạng mà mô hình có thể dự đoán
    # Sử dụng CountVectorizer đã được nạp
    reviews_vectorized = cv.transform(reviews_to_predict)

    # Dự đoán đánh giá từ mỗi mô hình
    nb_prediction = loaded_model.predict(reviews_vectorized)[0]
    logr_prediction = loaded_model_logistic.predict(reviews_vectorized)[0]

    MAX_SEQUENCE_LENGTH = 669  # Đặt giá trị MAX_SEQUENCE_LENGTH dựa trên quá trình huấn luyện
    sequences = tokenizer.texts_to_sequences(reviews_to_predict)
    padded_sequences = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH)
    lstm_predictions = lstm_model.predict(padded_sequences)
    
    return render_template('result.html', 
                           user_comment=review,
                           prediction_nb="Tích cực" if nb_prediction == 1 else "Tiêu cực",
                           prediction_logr="Tích cực" if logr_prediction == 1 else "Tiêu cực",
                           prediction_lstm="Tích cực" if lstm_predictions[0][1] > 0.5 else "Tiêu cực")
@app.route('/multipredict', methods=['POST'])
def multipredict():
    # Đọc bình luận từ tệp comments.txt
    with open('comments.txt', 'r', encoding='utf-8') as file:
        text = file.read()

    
    reviews = text.split('\n')

    reviews = [review for review in reviews if review.strip() and "Xem thêm" not in review]

    predictions = []
    #Multinomial Naive Bayes
    positive_count = 0
    negative_count = 0
    #Logistic Regression
    total_logistic_positive = 0
    total_logistic_negative = 0
    #LSTM
    total_lstm_positive = 0
    total_lstm_negative = 0

    for review in reviews:
        reviews_to_predict = [review.strip()]
        reviews_vectorized = cv.transform(reviews_to_predict)
         # Dự đoán đánh giá với Multinomial Naive Bayes
        prediction = loaded_model.predict(reviews_vectorized)[0]
        sentiment = "Tích cực" if prediction == 1 else "Tiêu cực"

          # Dự đoán đánh giá với Logistic Regression
        logr_prediction = loaded_model_logistic.predict(reviews_vectorized)[0]
        logr_sentiment = "Tích cực" if logr_prediction == 1 else "Tiêu cực"

         # Dự đoán đánh giá với LSTM
        MAX_SEQUENCE_LENGTH = 669  # Đặt giá trị MAX_SEQUENCE_LENGTH dựa trên quá trình huấn luyện
        sequences = tokenizer.texts_to_sequences(reviews_to_predict)
        padded_sequences = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH)

        threshold = 0.5  # Có thể thay đổi ngưỡng tùy theo yêu cầu

        lstm_predictions = lstm_model.predict(padded_sequences)
        lstm_sentiment = "Tích cực" if lstm_predictions[0][1] > threshold else "Tiêu cực"

        #predictions.append({"review": review, "predicted_sentiment": sentiment})

        # Tạo kết quả dự đoán
        predictions.append({
            "review": review,
            "predicted_sentiment": sentiment,
            "logr_sentiment": logr_sentiment,
            "lstm_sentiment": lstm_sentiment
        })    


        if prediction == 1:
            positive_count += 1
        else:
            negative_count += 1
        if logr_prediction == 1:
            total_logistic_positive += 1
        else:
            total_logistic_negative += 1
        if lstm_predictions[0][1] > threshold:
            total_lstm_positive += 1
        else:
            total_lstm_negative += 1      

    total_count = len(reviews)
    #NB
    positive_percentage = (positive_count / total_count) * 100
    negative_percentage = (negative_count / total_count) * 100
    #Logistic Reg
    positive__logr_percentage = (total_logistic_positive / total_count) * 100
    negative_logr_percentage = (total_logistic_negative / total_count) * 100
    #LSTM
    positive__lstm_percentage = (total_lstm_positive / total_count) * 100
    negative_lstm_percentage = (total_lstm_negative / total_count) * 100
    # Làm tròn tỷ lệ tích cực và tiêu cực
    positive_percentage = round(positive_percentage, 2)
    negative_percentage = round(negative_percentage, 2)

    positive__logr_percentage = round(positive__logr_percentage, 2)
    negative_logr_percentage = round(negative_logr_percentage, 2)

    positive__lstm_percentage = round(positive__lstm_percentage, 2)
    negative_lstm_percentage = round(negative_lstm_percentage, 2)

    #  # Tạo biểu đồ tròn NB
    # labels = ['Tích cực', 'Tiêu cực']
    # sizes = [positive_percentage, negative_percentage]
    # colors = ['lightgreen', 'lightcoral']

    # plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    # plt.axis('equal')  # Đảm bảo biểu đồ tròn

    #  # Tạo biểu đồ tròn Logr
    # labels = ['Tích cực', 'Tiêu cực']
    # sizes = [positive__logr_percentage, negative_logr_percentage]
    # colors = ['lightgreen', 'lightcoral']

    # plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    # plt.axis('equal')  # Đảm bảo biểu đồ tròn

    #  # Tạo biểu đồ tròn LSTM
    # labels = ['Tích cực', 'Tiêu cực']
    # sizes = [positive__lstm_percentage, negative_lstm_percentage]
    # colors = ['lightgreen', 'lightcoral']

    # plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    # plt.axis('equal')  # Đảm bảo biểu đồ tròn


    # # Lưu biểu đồ tròn vào một đối tượng BytesIO
    # img_buf = BytesIO()
    # plt.savefig(img_buf, format='png')
    # img_buf.seek(0)
    # img_data = base64.b64encode(img_buf.read()).decode()
    
    # return render_template('multiresult.html', predictions=predictions, total_count=total_count, positive_percentage=positive_percentage, negative_percentage=negative_percentage, pie_chart=img_data)
    # Tạo biểu đồ tròn NB
    labels_nb = ['Tích cực', 'Tiêu cực']
    sizes_nb = [positive_percentage, negative_percentage]
    colors_nb = ['lightgreen', 'lightcoral']

    plt.figure(figsize=(12, 4))  # Tạo một khung lớn để chứa ba biểu đồ tròn

    plt.subplot(131)  # Vị trí của biểu đồ tròn đầu tiên (Multinomial Naive Bayes)
    plt.pie(sizes_nb, labels=labels_nb, colors=colors_nb, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')  # Đảm bảo biểu đồ tròn
    plt.title('Multinomial Naive Bayes')

    # Tạo biểu đồ tròn Logr
    labels_logr = ['Tích cực', 'Tiêu cực']
    sizes_logr = [positive__logr_percentage, negative_logr_percentage]
    colors_logr = ['lightgreen', 'lightcoral']

    plt.subplot(132)  # Vị trí của biểu đồ tròn thứ hai (Logistic Regression)
    plt.pie(sizes_logr, labels=labels_logr, colors=colors_logr, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')  # Đảm bảo biểu đồ tròn
    plt.title('Logistic Regression')

    # Tạo biểu đồ tròn LSTM
    labels_lstm = ['Tích cực', 'Tiêu cực']
    sizes_lstm = [positive__lstm_percentage, negative_lstm_percentage]
    colors_lstm = ['lightgreen', 'lightcoral']

    plt.subplot(133)  # Vị trí của biểu đồ tròn thứ ba (LSTM)
    plt.pie(sizes_lstm, labels=labels_lstm, colors=colors_lstm, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')  # Đảm bảo biểu đồ tròn
    plt.title('LSTM')

    # Lưu biểu đồ tròn vào một đối tượng BytesIO
    img_buf = BytesIO()
    plt.savefig(img_buf, format='png')
    img_buf.seek(0)
    img_data = base64.b64encode(img_buf.read()).decode()

    return render_template('multiresult.html', predictions=predictions, total_count=total_count, positive_percentage=positive_percentage, negative_percentage=negative_percentage, pie_chart=img_data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
