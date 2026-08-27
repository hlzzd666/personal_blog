import logging

from backend.app.core.database import SessionLocal
from backend.app.services.daily_learning import process_daily_learning_tick


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    with SessionLocal() as session:
        result = process_daily_learning_tick(session)
    logging.getLogger(__name__).info("Daily learning tick finished: %s", result)


if __name__ == "__main__":
    main()
