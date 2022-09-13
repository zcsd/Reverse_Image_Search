FROM python:3.9-slim-bullseye
LABEL maintainer="Zichun"
COPY image_search/ /project/image_search/
COPY requirements.txt /project/
#COPY .towhee/ /root/.towhee/
#COPY .cache/ /root/.cache/
RUN cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo 'Asia/Shanghai' >/etc/timezone
ENV LANG C.UTF-8
ENV VECTORHOST host.docker.internal
RUN sed -i 8d /project/image_search/conf/config.ini && sed -i 7a\host:" "${VECTORHOST} /project/image_search/conf/config.ini
WORKDIR /project
RUN /usr/local/bin/pip3 install -r /project/requirements.txt && rm -r /root/.cache/pip 
EXPOSE 5000
CMD ["python3", "image_search/app.py"]