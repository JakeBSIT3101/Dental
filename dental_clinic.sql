-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Nov 26, 2025 at 12:54 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `dental_clinic`
--

-- --------------------------------------------------------

--
-- Table structure for table `appointments`
--

CREATE TABLE `appointments` (
  `appointment_id` int(11) NOT NULL,
  `patient_id` int(11) NOT NULL,
  `dentist_id` int(11) NOT NULL,
  `scheduled_at` datetime NOT NULL,
  `status` enum('scheduled','completed','cancelled','no_show') DEFAULT 'scheduled',
  `reason` varchar(255) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `appointments`
--

INSERT INTO `appointments` (`appointment_id`, `patient_id`, `dentist_id`, `scheduled_at`, `status`, `reason`, `notes`, `created_at`) VALUES
(21, 1, 2, '2025-02-03 09:00:00', 'completed', 'Fluoride Treatment', 'Child patient, no cavities detected. Advised 6-month recall.', '2025-11-25 14:14:47'),
(22, 2, 1, '2025-02-03 10:30:00', 'scheduled', 'Routine Cleaning', 'First visit to clinic, requested full mouth cleaning.', '2025-11-25 14:14:47'),
(23, 3, 2, '2025-02-04 14:00:00', 'scheduled', 'Dental Checkup', 'Mother reports occasional sensitivity on front teeth.', '2025-11-25 14:14:47'),
(24, 4, 3, '2025-02-05 15:30:00', 'completed', 'Orthodontic Consultation', 'Mild crowding, braces recommended. Patient considering options.', '2025-11-25 14:14:47'),
(25, 5, 7, '2025-02-06 09:15:00', 'scheduled', 'Dentures Evaluation', 'Existing dentures are loose; plan for relining.', '2025-11-25 14:14:47'),
(26, 6, 2, '2025-02-06 11:00:00', 'completed', 'Fluoride Application', 'Applied fluoride varnish, reinforced oral hygiene instructions.', '2025-11-25 14:14:47'),
(27, 7, 4, '2025-02-07 13:45:00', 'scheduled', 'Root Canal Assessment', 'Severe pain on lower molar, probable RCT.', '2025-11-25 14:14:47'),
(28, 8, 5, '2025-02-08 10:00:00', 'completed', 'Gum Treatment', 'Moderate periodontitis; started scaling and root planing.', '2025-11-25 14:14:47'),
(29, 9, 8, '2025-02-08 16:00:00', 'scheduled', 'Wisdom Tooth Extraction', 'Impacted lower third molar on radiograph.', '2025-11-25 14:14:47'),
(30, 10, 1, '2025-02-09 09:30:00', 'no_show', 'General Checkup', 'Patient did not arrive; to be rescheduled.', '2025-11-25 14:14:47');

-- --------------------------------------------------------

--
-- Table structure for table `appointment_treatments`
--

CREATE TABLE `appointment_treatments` (
  `id` int(11) NOT NULL,
  `appointment_id` int(11) NOT NULL,
  `treatment_id` int(11) NOT NULL,
  `fee` decimal(10,2) DEFAULT NULL,
  `notes` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `dentists`
--

CREATE TABLE `dentists` (
  `dentist_id` int(11) NOT NULL,
  `full_name` varchar(150) NOT NULL,
  `specialization` varchar(100) DEFAULT NULL,
  `phone` varchar(30) DEFAULT NULL,
  `email` varchar(120) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `dentists`
--

INSERT INTO `dentists` (`dentist_id`, `full_name`, `specialization`, `phone`, `email`, `is_active`, `created_at`) VALUES
(1, 'Dr. Maria Santos', 'General Dentistry', '09171234501', 'maria.santos@dclinic.com', 1, '2025-11-25 14:13:09'),
(2, 'Dr. John Reyes', 'Pediatric Dentistry', '09171234502', 'john.reyes@dclinic.com', 1, '2025-11-25 14:13:09'),
(3, 'Dr. Angela Mendoza', 'Orthodontics', '09171234503', 'angela.mendoza@dclinic.com', 1, '2025-11-25 14:13:09'),
(4, 'Dr. Patrick Cruz', 'Endodontics', '09171234504', 'patrick.cruz@dclinic.com', 1, '2025-11-25 14:13:09'),
(5, 'Dr. Raymond Javier', 'Periodontics', '09171234505', 'raymond.javier@dclinic.com', 1, '2025-11-25 14:13:09'),
(6, 'Dr. Jeanette Villanueva', 'Cosmetic Dentistry', '09171234506', 'jean.villanueva@dclinic.com', 1, '2025-11-25 14:13:09'),
(7, 'Dr. Paolo De Leon', 'Prosthodontics', '09171234507', 'paolo.deleon@dclinic.com', 1, '2025-11-25 14:13:09'),
(8, 'Dr. Carla Robles', 'Oral Surgery', '09171234508', 'carla.robles@dclinic.com', 1, '2025-11-25 14:13:09'),
(9, 'Dr. Francis Espino', 'Orthodontics', '09171234509', 'francis.espino@dclinic.com', 1, '2025-11-25 14:13:09'),
(10, 'Dr. Kristine Navarro', 'General Dentistry', '09171234510', 'kristine.navarro@dclinic.com', 0, '2025-11-25 14:13:09');

-- --------------------------------------------------------

--
-- Table structure for table `patients`
--

CREATE TABLE `patients` (
  `patient_id` int(11) NOT NULL,
  `first_name` varchar(100) NOT NULL,
  `last_name` varchar(100) NOT NULL,
  `birth_date` date DEFAULT NULL,
  `age_group` enum('child','adult','old') DEFAULT NULL,
  `gender` enum('male','female','other') DEFAULT NULL,
  `phone` varchar(30) DEFAULT NULL,
  `email` varchar(120) DEFAULT NULL,
  `address` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `patients`
--

INSERT INTO `patients` (`patient_id`, `first_name`, `last_name`, `birth_date`, `age_group`, `gender`, `phone`, `email`, `address`, `created_at`) VALUES
(1, 'Maria', 'Dela Cruz', '2016-05-12', 'child', 'female', '09123456701', 'maria.dc@example.com', 'Brgy. 4, Nasugbu, Batangas', '2025-11-25 14:12:12'),
(2, 'Joshua', 'Reyes', '1998-09-22', 'adult', 'male', '09123456702', 'josh.reyes@example.com', 'Brgy. 10, Lian, Batangas', '2025-11-25 14:12:12'),
(3, 'Alyssa', 'Torres', '2012-03-18', 'child', 'female', '09123456703', 'alyssa.torres@example.com', 'Brgy. 5, Tuy, Batangas', '2025-11-25 14:12:12'),
(4, 'Ricardo', 'Gonzales', '1985-11-30', 'adult', 'male', '09123456704', 'rich.gonzales@example.com', 'Brgy. 7, Calatagan, Batangas', '2025-11-25 14:12:12'),
(5, 'Antonio', 'Velasco', '1956-01-14', 'old', 'male', '09123456705', 'anton.velasco@example.com', 'Brgy. 2, Balayan, Batangas', '2025-11-25 14:12:12'),
(6, 'Sophia', 'Mendoza', '2015-08-07', 'child', 'female', '09123456706', 'sophia.mendoza@example.com', 'Brgy. 3, Batangas City', '2025-11-25 14:12:12'),
(7, 'Kristine', 'Ramos', '1993-06-25', 'adult', 'female', '09123456707', 'kristine.ramos@example.com', 'Brgy. 15, Lemery, Batangas', '2025-11-25 14:12:12'),
(8, 'Bernardo', 'Santos', '1952-04-09', 'old', 'male', '09123456708', 'bernard.santos@example.com', 'Brgy. 6, Nasugbu, Batangas', '2025-11-25 14:12:12'),
(9, 'Miguel', 'Castillo', '2004-12-02', 'adult', 'male', '09123456709', 'miguel.castillo@example.com', 'Brgy. 9, Palico, Batangas', '2025-11-25 14:12:12'),
(10, 'Angelica', 'Navarro', '1964-02-19', 'old', 'female', '09123456710', 'angel.nav@example.com', 'Brgy. 1, Balayan, Batangas', '2025-11-25 14:12:12'),
(11, 'adsd', 'asd', '0000-00-00', 'adult', '', 'sada', 'dasd', 'asdasd', '2025-11-25 23:11:15'),
(12, 'asda', 'sda', '0000-00-00', 'child', '', 'asdasd', 'as', 'dasda', '2025-11-25 23:15:41'),
(13, 'das', 'asd', '0000-00-00', 'old', '', 'asd', 'ads', 'adsd', '2025-11-25 23:17:32');

-- --------------------------------------------------------

--
-- Table structure for table `patient_history`
--

CREATE TABLE `patient_history` (
  `history_id` int(11) NOT NULL,
  `patient_id` int(11) NOT NULL,
  `appointment_id` int(11) DEFAULT NULL,
  `visit_date` datetime DEFAULT current_timestamp(),
  `diagnosis` text DEFAULT NULL,
  `treatment_given` text DEFAULT NULL,
  `prescription` text DEFAULT NULL,
  `follow_up_date` date DEFAULT NULL,
  `notes` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `payments`
--

CREATE TABLE `payments` (
  `payment_id` int(11) NOT NULL,
  `appointment_id` int(11) NOT NULL,
  `patient_id` int(11) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `payment_date` datetime DEFAULT current_timestamp(),
  `method` enum('cash','card','online','other') DEFAULT 'cash',
  `status` enum('pending','paid','refunded','cancelled') DEFAULT 'paid',
  `reference_no` varchar(100) DEFAULT NULL,
  `remarks` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `treatments`
--

CREATE TABLE `treatments` (
  `treatment_id` int(11) NOT NULL,
  `name` varchar(150) NOT NULL,
  `description` text DEFAULT NULL,
  `age_group` enum('child','adult','old','any') DEFAULT 'any',
  `default_fee` decimal(10,2) DEFAULT 0.00
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `treatments`
--

INSERT INTO `treatments` (`treatment_id`, `name`, `description`, `age_group`, `default_fee`) VALUES
(1, 'Cleaning', 'Basic dental cleaning', 'any', 800.00),
(2, 'Fluoride', 'Fluoride application', 'child', 500.00),
(3, 'Filling', 'Tooth filling', 'any', 1500.00),
(4, 'Extraction', 'Tooth extraction', 'any', 2000.00),
(5, 'Dentures', 'Full or partial dentures', 'old', 18000.00);

-- --------------------------------------------------------

--
-- Table structure for table `user_accounts`
--

CREATE TABLE `user_accounts` (
  `user_id` int(11) NOT NULL,
  `username` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('admin','dentist','staff','receptionist','patient') DEFAULT 'patient',
  `status` enum('active','inactive','banned') DEFAULT 'active',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `user_accounts`
--

INSERT INTO `user_accounts` (`user_id`, `username`, `password_hash`, `role`, `status`, `created_at`, `updated_at`) VALUES
(1, 'admin', 'admin123', 'admin', 'active', '2025-11-25 13:51:35', '2025-11-25 14:09:55'),
(2, 'dr.javier', '$2b$12$6lO0Yf8E1efKq8DkMxCq8eVh6UoX2oPFK5Xc5YI1JH8yNwP0zUq3W', 'dentist', 'active', '2025-11-25 13:51:35', '2025-11-25 13:51:35'),
(3, 'dr.mendoza', '$2b$12$6lO0Yf8E1efKq8DkMxCq8eVh6UoX2oPFK5Xc5YI1JH8yNwP0zUq3W', 'dentist', 'active', '2025-11-25 13:51:35', '2025-11-25 13:51:35'),
(4, 'reception.bella', '$2b$12$6lO0Yf8E1efKq8DkMxCq8eVh6UoX2oPFK5Xc5YI1JH8yNwP0zUq3W', 'receptionist', 'active', '2025-11-25 13:51:35', '2025-11-25 13:51:35'),
(5, 'staff.manny', '$2b$12$6lO0Yf8E1efKq8DkMxCq8eVh6UoX2oPFK5Xc5YI1JH8yNwP0zUq3W', 'staff', 'active', '2025-11-25 13:51:35', '2025-11-25 13:51:35'),
(6, 'patient.rose', '$2b$12$6lO0Yf8E1efKq8DkMxCq8eVh6UoX2oPFK5Xc5YI1JH8yNwP0zUq3W', 'patient', 'active', '2025-11-25 13:51:35', '2025-11-25 13:51:35'),
(7, 'patient.mike', '$2b$12$6lO0Yf8E1efKq8DkMxCq8eVh6UoX2oPFK5Xc5YI1JH8yNwP0zUq3W', 'patient', 'active', '2025-11-25 13:51:35', '2025-11-25 13:51:35'),
(8, 'patient.alyssa', '$2b$12$6lO0Yf8E1efKq8DkMxCq8eVh6UoX2oPFK5Xc5YI1JH8yNwP0zUq3W', 'patient', 'inactive', '2025-11-25 13:51:35', '2025-11-25 13:51:35'),
(9, 'dentist.ramos', '$2b$12$6lO0Yf8E1efKq8DkMxCq8eVh6UoX2oPFK5Xc5YI1JH8yNwP0zUq3W', 'dentist', 'active', '2025-11-25 13:51:35', '2025-11-25 13:51:35'),
(10, 'staff.louise', '$2b$12$6lO0Yf8E1efKq8DkMxCq8eVh6UoX2oPFK5Xc5YI1JH8yNwP0zUq3W', 'staff', 'banned', '2025-11-25 13:51:35', '2025-11-25 13:51:35');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `appointments`
--
ALTER TABLE `appointments`
  ADD PRIMARY KEY (`appointment_id`),
  ADD KEY `patient_id` (`patient_id`),
  ADD KEY `dentist_id` (`dentist_id`);

--
-- Indexes for table `appointment_treatments`
--
ALTER TABLE `appointment_treatments`
  ADD PRIMARY KEY (`id`),
  ADD KEY `appointment_id` (`appointment_id`),
  ADD KEY `treatment_id` (`treatment_id`);

--
-- Indexes for table `dentists`
--
ALTER TABLE `dentists`
  ADD PRIMARY KEY (`dentist_id`);

--
-- Indexes for table `patients`
--
ALTER TABLE `patients`
  ADD PRIMARY KEY (`patient_id`);

--
-- Indexes for table `patient_history`
--
ALTER TABLE `patient_history`
  ADD PRIMARY KEY (`history_id`),
  ADD KEY `patient_id` (`patient_id`),
  ADD KEY `appointment_id` (`appointment_id`);

--
-- Indexes for table `payments`
--
ALTER TABLE `payments`
  ADD PRIMARY KEY (`payment_id`),
  ADD KEY `appointment_id` (`appointment_id`),
  ADD KEY `patient_id` (`patient_id`);

--
-- Indexes for table `treatments`
--
ALTER TABLE `treatments`
  ADD PRIMARY KEY (`treatment_id`);

--
-- Indexes for table `user_accounts`
--
ALTER TABLE `user_accounts`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `appointments`
--
ALTER TABLE `appointments`
  MODIFY `appointment_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=31;

--
-- AUTO_INCREMENT for table `appointment_treatments`
--
ALTER TABLE `appointment_treatments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `dentists`
--
ALTER TABLE `dentists`
  MODIFY `dentist_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `patients`
--
ALTER TABLE `patients`
  MODIFY `patient_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT for table `patient_history`
--
ALTER TABLE `patient_history`
  MODIFY `history_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `payments`
--
ALTER TABLE `payments`
  MODIFY `payment_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `treatments`
--
ALTER TABLE `treatments`
  MODIFY `treatment_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `user_accounts`
--
ALTER TABLE `user_accounts`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `appointments`
--
ALTER TABLE `appointments`
  ADD CONSTRAINT `appointments_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`patient_id`),
  ADD CONSTRAINT `appointments_ibfk_2` FOREIGN KEY (`dentist_id`) REFERENCES `dentists` (`dentist_id`);

--
-- Constraints for table `appointment_treatments`
--
ALTER TABLE `appointment_treatments`
  ADD CONSTRAINT `appointment_treatments_ibfk_1` FOREIGN KEY (`appointment_id`) REFERENCES `appointments` (`appointment_id`),
  ADD CONSTRAINT `appointment_treatments_ibfk_2` FOREIGN KEY (`treatment_id`) REFERENCES `treatments` (`treatment_id`);

--
-- Constraints for table `patient_history`
--
ALTER TABLE `patient_history`
  ADD CONSTRAINT `patient_history_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`patient_id`),
  ADD CONSTRAINT `patient_history_ibfk_2` FOREIGN KEY (`appointment_id`) REFERENCES `appointments` (`appointment_id`);

--
-- Constraints for table `payments`
--
ALTER TABLE `payments`
  ADD CONSTRAINT `payments_ibfk_1` FOREIGN KEY (`appointment_id`) REFERENCES `appointments` (`appointment_id`),
  ADD CONSTRAINT `payments_ibfk_2` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`patient_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
