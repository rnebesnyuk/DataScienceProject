# PARKING-MANAGEMENT

## Overview

PARKING-MANAGEMENT is a web application designed to automatically identify vehicle license plate numbers from images, track the duration of parking for each vehicle, and calculate the accumulated parking costs.

## Features

PARKING-MANAGEMENT offers the following key features:

1. User Account Management:
   - Manage user accounts with distinct roles for administrators and regular users.
  
2. Role-Based Access Control:

   - Administrator Functions:
     - Add or delete registered vehicles with license plates.
     - Set up parking rates and lot spaces.
     - Create and manage a blacklist of vehicles.
     - Block the users
     - Grant the users with admin privileges

   - User Functions:
     - View personal license plate information.
     - Access parking history.
     - Enter/exit the parking lot by recognizing the license plates from the image

3. Image Processing and License Plate Detection:
   
   - Accept and process images submitted by users.
   - Detect and isolate the license plate area within the image.
   - Utilize Optical Character Recognition (OCR) to extract the license plate text from the image.

4. License Plate Verification:

   - Search the database for a registered vehicle by its license plate number.

5. Parking Duration Tracking:

   - Track the duration of parking by recording entry and exit times when a license plate is detected.

6. Parking Cost Calculation:

   - Calculate the total parking duration for each unique license plate.
   - Store duration data in the database associated with the license plate.
   - Calculate parking costs based on the duration.

7. Report Generation:

   - Generate detailed reports of parking duration and costs.
   - Export these reports in CSV format for further analysis.

## Installation Instructions from Git

1. Clone the Repository:
   
   Begin by cloning the repository to your local machine:
   ```bash
   git clone https://github.com/rnebesnyuk/DataScienceProject.git
   cd PARKING-MANAGEMENT
   ```
2. Set Up the Environment:
   
   Make sure you have Poetry installed. The project dependencies are managed via Poetry using the pyproject.toml and poetry.lock files.
   ```bash
   poetry install
   ```

3. Configure Environment Variables:
   
   Create a .env file in the root directory of the project and configure the necessary environment variables:

   - `DB_USER=` Username for accessing the database.
   - `DB_PASSWORD=` Password for accessing the database.
   - `DB_PORT=` Port number for the database connection.
   - `DB_NAME=` Name of the database.

   - `DB_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@localhost:${DB_PORT}/${DB_NAME}` URL for accessing the database.
   - `DB_LOCAL_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@localhost:${DB_PORT}/${DB_NAME}` URL local for accessing the database.

   - `SECRET_KEY=` A secret key used for cryptographic signing.
   - `ALGORITHM=` Desired cryptographic algorithm.

   - `MAIL_USERNAME=` Email for the mailing service host.
   - `MAIL_PASSWORD=` Password for the email host.
   - `MAIL_FROM=` Email from the specified address.
   - `MAIL_PORT=` SMTP port for email communication.
   - `MAIL_SERVER=` SMTP mailing service.

   - `REDIS_HOST=` Host for Redis database location.
   - `REDIS_LOCAL_HOST=` Local host for Redis database location.
   - `REDIS_PORT=` Port number for the Redis database connection.
   - `REDIS_PASSWORD=` Password for accessing the Redis database.

4. Start the Application

   The application is configured to start using Docker. Ensure you have Docker and Docker Compose installed.
   
   **Build and start the container:**
   ```bash
   docker-compose up --build
   ```
   
   **Once the container is running, the application will be accessible at:**
   ```bash
   http://localhost:7385/
   ```
   
   **The application is started inside the container using:**
    ```bash
    uvicorn main:app --port 7385 --reload
    ```

5. Database Migrations

   The database migrations are managed by Alembic and are located in the migrations folder. The migrations will automatically run when the container starts.

## Usage

Once the application is up and running, you can use tools like Postman or cURL to interact with the API at http://localhost:7385/.

1. Register for an initial account to create an administrator for access to administrative features.
2. Admin should set the parking rates (hourly rate, maximum daily rate) and limit available parking spaces.
3. Sign up as a user to register a vehicle and use a parking lot.
4. Ask the admin to add your vehicle to the database. Once the vehicle is added to the database, it can access the parking lot.
5. Now you can enter or leave the parking lot by reading the image with your car and the license plate number clearly visible.

<img src="https://github.com/user-attachments/assets/2f5f1066-ef4a-4b85-9e1c-c44819522ebb" alt="20240818_" width="500" height="375" /><img src="https://github.com/user-attachments/assets/122e53da-8070-4347-a9fb-7a1b94ae1cfb" alt="license_plates_detections_" width="500" height="375" />

<img src="https://github.com/user-attachments/assets/344547dc-db8c-4e64-9716-286c6ab390df" alt="20240818_080210" width="500" height="375" /><img src="https://github.com/user-attachments/assets/ca512f0b-ecea-4836-acad-dcac1d51c024" alt="license_plates_detections" width="500" height="375" />

5. Once entered or left the parking lot, the parking time is automatically calculated. Upon leaving, the total duration and cost for the parking is provided.
6. All parking records are stored in the database and can be accessed by admin, as well as downloaded in .csv for a certain license plate.
7. All currently parked vehicles can be checked by admin.
8. Additionally, vehicles can be blacklisted from entering the lot by the Admin.

## License

This project is licensed under the MIT License.
