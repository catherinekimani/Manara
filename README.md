# Manara

A comprehensive platform designed for commuters and PSV operators, offering real-time bus tracking, destination search, and Sacco management for optimized transport experiences.

## Table of Contents

- [Manara](#manara)
	- [Table of Contents](#table-of-contents)
	- [Requirements](#requirements)
	- [Installation](#installation)
		- [1. Clone the repository](#1-clone-the-repository)
	- [2. Set up a virtual environment](#2-set-up-a-virtual-environment)
	- [3. Install dependencies](#3-install-dependencies)
	- [4. Configure the database](#4-configure-the-database)
	- [5. Apply migrations](#5-apply-migrations)
	- [6. Run the Development Server](#6-run-the-development-server)
	- [7. You can access the API endpoints documentation at:](#7-you-can-access-the-api-endpoints-documentation-at)


## Requirements

- Python 3.10 or higher
- Django 4.x or higher
- PostgreSQL (or another database of your choice)
- pip (Python package installer)
- Virtual environment

## Installation

Follow these steps to get the project up & running locally:

### 1. Clone the repository

First, clone the repository from GitHub:

```bash
git clone https://github.com/catherinekimani/Manara.git

cd manara
```

## 2. Set up a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

## 3. Install dependencies
```bash
pip install -r requirements.txt
```

<p>If you don't have a requirements.txt file, you can generate one with:</p>

```bash
pip freeze > requirements.txt
```

## 4. Configure the database
<p>Make sure you have PostgreSQL (or your preferred database) installed and running locally. If you are using PostgreSQL, create a new database:</p>

```bash
psql -U postgres
CREATE DATABASE manara;
```

## 5. Apply migrations
Run the migrations to set up the database schema:

```bash
python manage.py makemigrations
python manage.py migrate
```

## 6. Run the Development Server

```bash
python3 manage.py runserver
```

## 7. You can access the API endpoints documentation at:

```bash
http://127.0.0.1:8000/swagger
```

