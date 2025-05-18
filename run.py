import uvicorn
import argparse

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument("--reload", action="store_true", help="Run with reload")

  args = parser.parse_args()

  reload = args.reload or False

  uvicorn.run("app.main:app", reload=reload, factory=False, port=5000)