from flask import Flask, request, Response
from selenium.common.exceptions import TimeoutException

from src.bot.hitesb2b import HitesB2b
from . import make_celery

app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL='redis://redis:6379',
    CELERY_RESULT_BACKEND='redis://redis:6379'
)
celery = make_celery(app)


@celery.task(autoretry_for=(TimeoutException,), retry_kwargs={
    'max_retries': 5
})
def run_b2b_hites_bot(user, password, start_date, end_date):
    print('parsing for user:', user)
    driver = HitesB2b()
    driver.login(user, password)
    one = driver.download_first_file(start_date, end_date)
    two = driver.download_second()
    third = driver.download_third_file()
    print('done parsing for user:', user)
    return one, two, third


@app.route('/bot/b2b/hites', methods=['POST'])
def response():
    req = request.get_json()
    if req.get('username') and req.get('password') and req.get('start_date') and req.get('end_date'):
        run_b2b_hites_bot.delay(req.get('username'), req.get('password'), req.get('start_date'), req.get('end_date'))
        return Response(status=201, headers={
            'X-Developed-by': 'Ammadkhalid'
        })
