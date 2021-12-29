FROM python:3.10-alpine

COPY psi-project/ /app/

CMD ["/usr/bin/python", "-m", "app"]
