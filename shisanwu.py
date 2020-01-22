import os
import sys
from dotenv import load_dotenv
import click
from flask_migrate import Migrate
from flask_cors import CORS
from app import create_app, db, global_cache
from app.models import Permission, User
from app.models import OutdoorSpot, OutdoorRecord, ClimateArea, Location
from app.models import Project, ProjectDetail, Company
from app.models import Spot, SpotRecord, Device
from app.models import gen_fake_db


# load environment var
dotenv_path = os.path.join(os.path.dirname(__name__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

app = create_app(os.getenv("FLASK_CONFIG") or 'default')
migrate = Migrate(app, db)
CORS(app, resources={r'/*': {'origins': '*'}})


COV = None
if os.environ.get("FLASK_COVERAGE"):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

# init admin in databse

# init cache


@app.shell_context_processor
def make_shell_context():
    return dict(
        db=db,
        User=User,
        Permission=Permission,
        OutdoorSpot=OutdoorSpot,
        OutdoorRecord=OutdoorRecord,
        ClimateArea=ClimateArea,
        Project=Project,
        ProjectDetail=ProjectDetail,
        Company=Company,
        Device=Device,
        Location=Location,
        Spot=Spot,
        SpotRecord=SpotRecord,
        gen_fake_db=gen_fake_db,
        global_cache=global_cache)


@app.cli.command()
@click.option('--coverage/--no-coverage', default=False, help='Run coverage test')
@click.argument('test_names', nargs=-1)
def test(coverage, test_names):
    """run unit tests."""
    if coverage and not os.environ.get("FLASK_COVERAGE"):
        import subprocess
        os.environ["FLASK_COVERAGE"] = "1"
        sys.exit(subprocess.call(sys.argv))

    import unittest
    if test_names:
        tests = unittest.TestLoader().loadTestsFromNames(test_names)
    else:
        tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print("Coverage Summary:")
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print("HTML version: file://%s/index/html" % covdir)
        COV.erase()


