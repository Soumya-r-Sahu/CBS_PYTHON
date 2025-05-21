-- Mobile Banking Procedures for Core Banking System
-- Contains stored procedures related to mobile banking operations
-- Created: May 21, 2025

DELIMITER $$

-- Procedure: Register Mobile Banking User
DROP PROCEDURE IF EXISTS register_mobile_banking_user$$
CREATE PROCEDURE register_mobile_banking_user(
    IN p_customer_id VARCHAR(20),
    IN p_device_id VARCHAR(100),
    IN p_device_model VARCHAR(100),
    IN p_device_os VARCHAR(50),
    IN p_os_version VARCHAR(20),
    IN p_app_version VARCHAR(20),
    IN p_fcm_token VARCHAR(255),
    OUT p_mb_user_id VARCHAR(36),
    OUT p_activation_code VARCHAR(10),
    OUT p_status VARCHAR(20),
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_exists INT DEFAULT 0;
    DECLARE v_customer_status VARCHAR(50);
    
    -- Generate UUID and activation code
    SET p_mb_user_id = UUID();
    SET p_activation_code = LPAD(FLOOR(RAND() * 1000000), 6, '0');
    
    -- Check if customer exists and is active
    SELECT COUNT(*), status INTO v_exists, v_customer_status
    FROM cbs_customers 
    WHERE customer_id = p_customer_id;
    
    IF v_exists = 0 THEN
        SET p_status = 'FAILED';
        SET p_message = 'Customer does not exist';
    ELSEIF v_customer_status != 'ACTIVE' THEN
        SET p_status = 'FAILED';
        SET p_message = CONCAT('Customer status is ', v_customer_status, '. Registration not allowed');
    ELSE
        -- Check if device is already registered
        SELECT COUNT(*) INTO v_exists
        FROM cbs_mobile_banking_users
        WHERE customer_id = p_customer_id 
        AND device_id = p_device_id;
        
        IF v_exists > 0 THEN
            -- Update existing registration
            UPDATE cbs_mobile_banking_users
            SET 
                device_model = p_device_model,
                device_os = p_device_os,
                os_version = p_os_version,
                app_version = p_app_version,
                fcm_token = p_fcm_token,
                activation_code = p_activation_code,
                activation_code_expiry = DATE_ADD(NOW(), INTERVAL 15 MINUTE),
                status = 'PENDING_ACTIVATION'
            WHERE 
                customer_id = p_customer_id 
                AND device_id = p_device_id;
                
            -- Get existing mb_user_id
            SELECT mb_user_id INTO p_mb_user_id
            FROM cbs_mobile_banking_users
            WHERE customer_id = p_customer_id 
            AND device_id = p_device_id;
            
            SET p_status = 'SUCCESS';
            SET p_message = 'Device re-registration successful. Activation code has been sent.';
        ELSE
            -- Insert new registration
            INSERT INTO cbs_mobile_banking_users (
                mb_user_id,
                customer_id,
                device_id,
                device_model,
                device_os,
                os_version,
                app_version,
                fcm_token,
                status,
                registered_at,
                activation_code,
                activation_code_expiry
            ) VALUES (
                p_mb_user_id,
                p_customer_id,
                p_device_id,
                p_device_model,
                p_device_os,
                p_os_version,
                p_app_version,
                p_fcm_token,
                'PENDING_ACTIVATION',
                NOW(),
                p_activation_code,
                DATE_ADD(NOW(), INTERVAL 15 MINUTE)
            );
            
            SET p_status = 'SUCCESS';
            SET p_message = 'Registration successful. Activation code has been sent.';
        END IF;
        
        -- Insert notification for customer
        INSERT INTO cbs_notifications (
            notification_id,
            user_id,
            user_type,
            title,
            message,
            notification_type,
            status,
            created_at
        ) VALUES (
            UUID(),
            p_customer_id,
            'CUSTOMER',
            'Mobile Banking Registration',
            CONCAT('You have registered a new device for mobile banking. If this was not you, please contact customer care immediately.'),
            'SECURITY',
            'UNREAD',
            NOW()
        );
    END IF;
END$$

-- Procedure: Activate Mobile Banking User
DROP PROCEDURE IF EXISTS activate_mobile_banking_user$$
CREATE PROCEDURE activate_mobile_banking_user(
    IN p_mb_user_id VARCHAR(36),
    IN p_activation_code VARCHAR(10),
    OUT p_status VARCHAR(20),
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_code VARCHAR(10);
    DECLARE v_expiry DATETIME;
    DECLARE v_customer_id VARCHAR(20);
    
    -- Get activation code details
    SELECT activation_code, activation_code_expiry, customer_id
    INTO v_code, v_expiry, v_customer_id
    FROM cbs_mobile_banking_users
    WHERE mb_user_id = p_mb_user_id;
    
    IF v_code IS NULL THEN
        SET p_status = 'FAILED';
        SET p_message = 'Invalid mobile banking user ID';
    ELSEIF v_code != p_activation_code THEN
        SET p_status = 'FAILED';
        SET p_message = 'Invalid activation code';
    ELSEIF NOW() > v_expiry THEN
        SET p_status = 'FAILED';
        SET p_message = 'Activation code expired';
    ELSE
        -- Activate mobile banking user
        UPDATE cbs_mobile_banking_users
        SET 
            status = 'ACTIVE',
            activation_code = NULL,
            activation_code_expiry = NULL
        WHERE mb_user_id = p_mb_user_id;
        
        -- Insert notification
        INSERT INTO cbs_notifications (
            notification_id,
            user_id,
            user_type,
            title,
            message,
            notification_type,
            status,
            created_at
        ) VALUES (
            UUID(),
            v_customer_id,
            'CUSTOMER',
            'Mobile Banking Activated',
            'Your mobile banking has been successfully activated. You can now use all mobile banking features.',
            'INFO',
            'UNREAD',
            NOW()
        );
        
        SET p_status = 'SUCCESS';
        SET p_message = 'Mobile banking activation successful';
    END IF;
END$$

DELIMITER ;
