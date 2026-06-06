FROM python:3.11

# set working directory
WORKDIR /app

# copy project
COPY . .

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# expose port
EXPOSE 8000

# run app
CMD ["uvicorn", "retrieval_api:app", "--host", "0.0.0.0", "--port", "8000"]