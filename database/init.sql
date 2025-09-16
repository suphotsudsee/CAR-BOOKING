-- Office Vehicle Booking System Database Initialization
-- This script sets up the initial database configuration

-- Set character set and collation
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- Create database if not exists (handled by Docker environment variables)
-- USE vehicle_booking;

-- Set timezone
SET time_zone = '+07:00';

-- Create initial admin user (will be handled by application migration)
-- This is just a placeholder for any initial setup needed