import sqlite3 as sql
from typing import Optional, List, Dict, Any, Tuple

DB_PATH = "C:/Users/Jason/source/repos/Project_Repo/Project_Repository/Flask_PWA_Template/database/data_source.db"


def _get_conn():
    conn = sql.connect(DB_PATH)
    conn.row_factory = sql.Row
    return conn


# Listings / attractions


def listListing() -> List[sql.Row]:
    conn = _get_conn()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM Listings").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_listings() -> List[Dict[str, Any]]:
    conn = _get_conn()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM Listings ORDER BY Date_entered DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_listing_by_id(listing_id: int) -> Optional[Dict[str, Any]]:
    conn = _get_conn()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT * FROM Listings WHERE Listings_ID = ?", (listing_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_listing_by_category(category_id: int) -> List[Tuple]:
    conn = _get_conn()
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT * FROM Listings WHERE Category_ID = ?", (category_id,)
    ).fetchall()
    conn.close()
    return rows


def get_attraction_by_listing_id(listing_id: int) -> Optional[Dict[str, Any]]:
    conn = _get_conn()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT * FROM Attractions WHERE Listings_ID = ?", (listing_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def get_average_rating(listing_id: int) -> Optional[float]:
    conn = _get_conn()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT AVG(Post_Rating) as avg_rating FROM Posts WHERE Listings_ID = ?", (listing_id,)
    ).fetchone()
    conn.close()
    return row["avg_rating"] if row and row["avg_rating"] is not None else None

def get_images_for_listing(listing_id: int) -> List[str]:
    conn = _get_conn()
    cur = conn.cursor()
    try:
        rows = cur.execute(
            "SELECT Image_URL FROM Listings_Images WHERE Listings_ID = ?", (listing_id,)
        ).fetchall()
        urls = [r["Image_URL"] for r in rows if r["Image_URL"]]
        conn.close()
        return urls
    except sql.Error:
        row = conn.execute(
            "SELECT Image FROM Listings WHERE Listings_ID = ?", (listing_id,)
        ).fetchone()
        conn.close()
        if row and row["Image"]:
            return [row["Image"]]
        return []

# Posts for Listing

def get_post_by_listing(listings_id: int) -> List[Tuple]:
    conn = _get_conn()
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT Text,Post_Rating,Date,Likes_Count,Comments_Count,Username FROM Posts JOIN Users ON Posts.User_ID = Users.User_ID WHERE Listings_ID = ?", (listings_id,)
    ).fetchall()
    conn.close()
    return rows


# User


def create_user(
    username: str,
    email: str,
    password_hash: str,
    Date_of_birth=None,
    Address_ID=None,
    First_name=None,
    Surname=None,
    Profile_Photo=None,
) -> Optional[int]:
    """
    Insert a new user. Returns new User_ID on success, None on integrity error (duplicate).
    Expects Users table to have a column named password_hash.
    """
    sql_insert = """
    INSERT INTO Users
      (Username, password_hash, Email, Date_of_birth, Address_ID, First_name, Surname, Profile_Photo)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            sql_insert,
            (
                username,
                password_hash,
                email,
                Date_of_birth,
                Address_ID,
                First_name,
                Surname,
                Profile_Photo,
            ),
        )
        conn.commit()
        return cur.lastrowid
    except sql.IntegrityError:
        return None
    finally:
        conn.close()


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Users WHERE Username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Users WHERE User_ID = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# Optional Stuff I asked AI for


def ensure_tables_exist():
    """Create minimal tables if they don't exist (useful for development)."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.executescript(
        """
    CREATE TABLE IF NOT EXISTS Listings (
      Listings_ID INTEGER PRIMARY KEY,
      Location TEXT,
      Price NUMERIC,
      Title TEXT,
      Description TEXT,
      Image TEXT,
      Category_ID INTEGER,
      Date_entered NUMERIC,
      Link_URL TEXT
    );

    CREATE TABLE IF NOT EXISTS Attractions (
      Listings_ID INTEGER PRIMARY KEY REFERENCES Listings(Listings_ID) ON DELETE CASCADE,
      Type TEXT,
      Title TEXT,
      Entry_Fee NUMERIC,
      Opening_Hours TEXT,
      Description TEXT,
      Address_ID INTEGER
    );

    CREATE TABLE IF NOT EXISTS Listings_Images (
      Image_ID INTEGER PRIMARY KEY,
      Listings_ID INTEGER NOT NULL REFERENCES Listings(Listings_ID) ON DELETE CASCADE,
      Image_URL TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS Users (
      User_ID INTEGER PRIMARY KEY,
      Username TEXT UNIQUE,
      password_hash TEXT,
      Email TEXT UNIQUE,
      Date_of_birth NUMERIC,
      Address_ID INTEGER,
      First_name TEXT,
      Surname TEXT,
      Profile_Photo BLOB,
      is_active INTEGER DEFAULT 1,
      created_at TEXT DEFAULT (datetime('now'))
    );
    """
    )
    conn.commit()
    conn.close()
