
# Open Source Gacha Cards!

## How to Use

1.  **Download the source code.**
2.  **Install Dependencies**: Make sure you have all the necessary dependencies listed at the top of the `main.py` file installed.
3.  **Navigate to the Folder**: Open your command prompt and go to the folder containing the source code.
4.  **Run the Server**: Type `flask --app main run` and press Enter.
5.  **Access the Application**: Click the link that appears in your command prompt.

## Notes for modding:

# Notes for `settings.json`

* When adding **pools**, the cards in those pools **must** also be listed in the `CARDS` array.
* **Example Pool**: In `pool 1`, `Card` has a 90% draw chance, `Card2` has 9%, and `Card3` has 1%.
* A **default card** needs to be set for players entering a match with an empty slot.

# Notes for `cards.py`

* When adding **custom cards**, they must have a corresponding **class** in the `cards.py` file.
* The **CLASS NAME** of this class needs to be entered as a **string** in the `CARDS` array (see `settings.json`).
* Custom cards should also have a corresponding **CSS class** (see `cards.css` and `cards.js`).

# Notes for `cards.js` (`/static/cards.js`)

* For the `cardFinder` object:
    * The **key** should match the **class name** written in the `CARDS` array (see `settings.json`).
    * The `className` property should match the **CSS class** you want to assign to your custom card (see `cards.css`).
    * `cardName` is the **display name** of your card. It's recommended to match it with the name you gave your custom card in `cards.py` for consistency.

# File Paths

* `cards.js`: `/static/cards.js`
* `cards.css`: `/static/css/cards.css`

## What?

Open Source Gacha Cards is cross-platform browser a card game i started developing on Mar 24, 2025. It is mean to be a gacha game that is ethical and does not exploit the player for money, hence why it is open source. In this game you can host your own servers which Players can connect to play with others that are on the same server. Planned features include card trading, equipment, limited card supply, and a pve campeign

## Why?

I always loved how fun gacha games are, but hated predatory practices with a passion (eg. absurdly priced microtransactions, multiple currencies, annoying popups), so i decided to make my own game mostly inspired by Genshin's TCG and irl trading cards. I originally wanted to find a game that is one time purchase, has no time-gating, grindy, has pvp, and most importantly, has gacha elements. But after scouring the internet and all available app stores, i found exactly 0 of them that met even half my criteria. I had just thought that there was no demand for such game, but after going on multiple forums, i soon discovered a multitude of posts of people asking if such a game existed, so i decided to make my own.

## When?

Idk its done when its done

## How to contribute?

DM me on Discord or sth @someone6682