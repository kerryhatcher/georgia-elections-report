from builders import county_boards, demographics, turnout


def main() -> None:
    county_boards.build()
    turnout.build()
    demographics.build()


if __name__ == "__main__":
    main()
