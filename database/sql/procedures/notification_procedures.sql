-- Notification Procedures for Core Banking System
-- Contains stored procedures related to notification operations
-- Created: May 21, 2025

DELIMITER $$

-- Procedure: Send notification to customer
DROP PROCEDURE IF EXISTS send_customer_notification$$
CREATE PROCEDURE send_customer_notification(
    IN p_customer_id VARCHAR(20),
    IN p_title VARCHAR(255),
    IN p_message TEXT,
    IN p_notification_type ENUM('INFO','ALERT','WARNING','PROMOTION','SECURITY'),
    OUT p_notification_id VARCHAR(36),
    OUT p_status VARCHAR(20)
)
BEGIN
    -- Generate notification ID
    SET p_notification_id = UUID();
    
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
        p_notification_id,
        p_customer_id,
        'CUSTOMER',
        p_title,
        p_message,
        p_notification_type,
        'UNREAD',
        NOW()
    );
    
    -- Set status
    SET p_status = 'SENT';
END$$

-- Procedure: Mark notification as read
DROP PROCEDURE IF EXISTS mark_notification_read$$
CREATE PROCEDURE mark_notification_read(
    IN p_notification_id VARCHAR(36),
    IN p_user_id VARCHAR(20),
    OUT p_status VARCHAR(20),
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_count INT DEFAULT 0;
    
    -- Check if notification exists for the user
    SELECT COUNT(*) INTO v_count
    FROM cbs_notifications
    WHERE notification_id = p_notification_id
    AND user_id = p_user_id;
    
    IF v_count = 0 THEN
        SET p_status = 'FAILED';
        SET p_message = 'Notification not found';
    ELSE
        -- Mark as read
        UPDATE cbs_notifications
        SET 
            status = 'READ',
            read_at = NOW()
        WHERE 
            notification_id = p_notification_id
            AND user_id = p_user_id;
            
        SET p_status = 'SUCCESS';
        SET p_message = 'Notification marked as read';
    END IF;
END$$

-- Procedure: Get unread notification count
DROP PROCEDURE IF EXISTS get_unread_notification_count$$
CREATE PROCEDURE get_unread_notification_count(
    IN p_user_id VARCHAR(20),
    IN p_user_type ENUM('CUSTOMER','ADMIN','EMPLOYEE'),
    OUT p_count INT
)
BEGIN
    SELECT COUNT(*) INTO p_count
    FROM cbs_notifications
    WHERE user_id = p_user_id
    AND user_type = p_user_type
    AND status = 'UNREAD';
END$$

DELIMITER ;
