"""
Recruitment Module

This module handles all recruitment-related functionalities including:
- Managing job openings
- Application tracking
- Interview scheduling
- Candidate evaluation
- Onboarding process
"""

import os
import sys
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import uuid
import json
import shutil

# Use relative imports instead of modifying sys.path
# Import HR-ERP modules
from ..config import RECRUITMENT_SETTINGS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('hr-recruitment')


class RecruitmentManager:
    """Recruitment management for HR-ERP system"""
    
    def __init__(self):
        """Initialize the recruitment manager"""
        self.db_connection = None
        self._initialize_db_connection()
        self._ensure_storage_path()
    
    def _initialize_db_connection(self):
        """Initialize database connection"""
        try:
            # Import database connection
            # Commented out direct sys.path modification
            # # Removed: sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from utils.lib.packages import fix_path
            fix_path()
            from utils.lib.packages import import_module
            DatabaseConnection = import_module("database.python.connection").DatabaseConnection
            
            self.db_connection = DatabaseConnection()
            logger.info("Database connection initialized for recruitment")
            
        except ImportError:
            logger.error("Failed to import DatabaseConnection")
    
    def _ensure_storage_path(self):
        """Ensure resume storage path exists"""
        try:
            storage_path = Path(RECRUITMENT_SETTINGS['resume_storage_path'])
            os.makedirs(storage_path, exist_ok=True)
            logger.info(f"Resume storage path ensured: {storage_path}")
            
        except Exception as e:
            logger.error(f"Error ensuring storage path: {e}")
    
    def create_job_opening(self, job_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new job opening
        
        Args:
            job_data: Job opening details
            
        Returns:
            Job ID if successful, None otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return None
            
            cursor = conn.cursor()
            
            # Generate job ID
            job_id = f"JOB-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            # Extract basic job information
            title = job_data.get('title', '')
            department = job_data.get('department', '')
            location = job_data.get('location', '')
            job_type = job_data.get('job_type', 'Full-time')
            positions = job_data.get('positions', 1)
            description = job_data.get('description', '')
            requirements = job_data.get('requirements', '')
            responsibilities = job_data.get('responsibilities', '')
            
            # Set posting and closing dates
            posting_date = job_data.get('posting_date', datetime.datetime.now().date())
            closing_date = job_data.get('closing_date')
            
            # Insert job record
            query = """
                INSERT INTO hr_job_openings (
                    job_id, title, department, location,
                    job_type, positions, description, requirements,
                    responsibilities, posting_date, closing_date,
                    status, created_date
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                )
            """
            
            cursor.execute(query, (
                job_id, title, department, location,
                job_type, positions, description, requirements,
                responsibilities, posting_date, closing_date,
                'Open'
            ))
            
            # Insert qualification requirements if provided
            if 'qualifications' in job_data:
                quals = job_data['qualifications']
                
                if isinstance(quals, list):
                    for qual in quals:
                        qual_query = """
                            INSERT INTO hr_job_qualifications (
                                job_id, qualification_type, description,
                                is_required
                            ) VALUES (%s, %s, %s, %s)
                        """
                        
                        cursor.execute(qual_query, (
                            job_id,
                            qual.get('type', 'Education'),
                            qual.get('description', ''),
                            1 if qual.get('required', True) else 0
                        ))
            
            # Insert required approvals
            for approver_role in RECRUITMENT_SETTINGS['required_approvals_for_hiring']:
                approval_query = """
                    INSERT INTO hr_job_approvals (
                        job_id, approver_role, status
                    ) VALUES (%s, %s, %s)
                """
                
                cursor.execute(approval_query, (
                    job_id, approver_role, 'Pending'
                ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Created new job opening: {job_id} - {title}")
            return job_id
            
        except Exception as e:
            logger.error(f"Error creating job opening: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return None
    
    def get_job_opening(self, job_id: str) -> Dict[str, Any]:
        """
        Get job opening details
        
        Args:
            job_id: Job ID
            
        Returns:
            Job opening details
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return {}
            
            cursor = conn.cursor(dictionary=True)
            
            # Get job details
            query = """
                SELECT *
                FROM hr_job_openings
                WHERE job_id = %s
            """
            
            cursor.execute(query, (job_id,))
            job = cursor.fetchone()
            
            if not job:
                logger.warning(f"Job {job_id} not found")
                return {}
            
            # Get qualification requirements
            qual_query = """
                SELECT *
                FROM hr_job_qualifications
                WHERE job_id = %s
            """
            
            cursor.execute(qual_query, (job_id,))
            qualifications = cursor.fetchall()
            job['qualifications'] = qualifications or []
            
            # Get approval status
            approval_query = """
                SELECT *
                FROM hr_job_approvals
                WHERE job_id = %s
            """
            
            cursor.execute(approval_query, (job_id,))
            approvals = cursor.fetchall()
            job['approvals'] = approvals or []
            
            # Get application count
            app_count_query = """
                SELECT COUNT(*) AS application_count
                FROM hr_job_applications
                WHERE job_id = %s
            """
            
            cursor.execute(app_count_query, (job_id,))
            count_data = cursor.fetchone()
            job['application_count'] = count_data['application_count'] if count_data else 0
            
            cursor.close()
            
            return job
            
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
            return {}
    
    def update_job_status(self, job_id: str, status: str, reason: str = "") -> bool:
        """
        Update job opening status
        
        Args:
            job_id: Job ID
            status: New status
            reason: Reason for status change
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor()
            
            # Update job status
            query = """
                UPDATE hr_job_openings
                SET status = %s, last_modified = NOW()
                WHERE job_id = %s
            """
            
            cursor.execute(query, (status, job_id))
            
            # Record status change
            log_query = """
                INSERT INTO hr_job_status_log (
                    job_id, status, change_date, reason
                ) VALUES (%s, %s, NOW(), %s)
            """
            
            cursor.execute(log_query, (job_id, status, reason))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Updated job {job_id} status to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating job {job_id} status: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return False
    
    def create_application(self, application_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new job application
        
        Args:
            application_data: Application details
            
        Returns:
            Application ID if successful, None otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return None
            
            cursor = conn.cursor()
            
            # Generate application ID
            application_id = f"APP-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            # Extract basic application information
            job_id = application_data.get('job_id')
            candidate_name = application_data.get('candidate_name', '')
            email = application_data.get('email', '')
            phone = application_data.get('phone', '')
            current_company = application_data.get('current_company', '')
            current_position = application_data.get('current_position', '')
            experience_years = application_data.get('experience_years', 0)
            current_salary = application_data.get('current_salary', 0)
            expected_salary = application_data.get('expected_salary', 0)
            cover_letter = application_data.get('cover_letter', '')
            
            # Default stage is Application
            current_stage = RECRUITMENT_SETTINGS['stages'][0]
            
            # Check if the job exists and is open
            check_job_query = """
                SELECT status 
                FROM hr_job_openings 
                WHERE job_id = %s
            """
            
            cursor.execute(check_job_query, (job_id,))
            job_status = cursor.fetchone()
            
            if not job_status or job_status[0] != 'Open':
                logger.warning(f"Job {job_id} not open for applications")
                return None
            
            # Insert application record
            query = """
                INSERT INTO hr_job_applications (
                    application_id, job_id, candidate_name, email,
                    phone, current_company, current_position,
                    experience_years, current_salary, expected_salary,
                    cover_letter, current_stage, application_date,
                    status
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s
                )
            """
            
            cursor.execute(query, (
                application_id, job_id, candidate_name, email,
                phone, current_company, current_position,
                experience_years, current_salary, expected_salary,
                cover_letter, current_stage, 'Submitted'
            ))
            
            # Process resume if provided
            if 'resume' in application_data:
                resume_path = self._save_resume_file(
                    application_id,
                    application_data['resume']
                )
                
                if resume_path:
                    update_resume_query = """
                        UPDATE hr_job_applications
                        SET resume_path = %s
                        WHERE application_id = %s
                    """
                    
                    cursor.execute(update_resume_query, (resume_path, application_id))
            
            # Store candidate education if provided
            if 'education' in application_data:
                education_records = application_data['education']
                
                if isinstance(education_records, list):
                    for edu in education_records:
                        edu_query = """
                            INSERT INTO hr_candidate_education (
                                application_id, degree, institution, 
                                major, year_completed, grade
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        
                        cursor.execute(edu_query, (
                            application_id,
                            edu.get('degree', ''),
                            edu.get('institution', ''),
                            edu.get('major', ''),
                            edu.get('year_completed'),
                            edu.get('grade', '')
                        ))
            
            # Store work experience if provided
            if 'experience' in application_data:
                experience_records = application_data['experience']
                
                if isinstance(experience_records, list):
                    for exp in experience_records:
                        exp_query = """
                            INSERT INTO hr_candidate_experience (
                                application_id, company_name, position,
                                start_date, end_date, responsibilities
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        
                        # Process dates
                        start_date = exp.get('start_date')
                        end_date = exp.get('end_date')
                        
                        cursor.execute(exp_query, (
                            application_id,
                            exp.get('company', ''),
                            exp.get('position', ''),
                            start_date,
                            end_date,
                            exp.get('responsibilities', '')
                        ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Created new application: {application_id} for job {job_id}")
            return application_id
            
        except Exception as e:
            logger.error(f"Error creating application: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return None
    
    def _save_resume_file(self, application_id: str, resume_data: Dict[str, Any]) -> Optional[str]:
        """
        Save resume file
        
        Args:
            application_id: Application ID
            resume_data: Resume file data
            
        Returns:
            File path if successful, None otherwise
        """
        try:
            # Get file content and name
            content = resume_data.get('content')
            file_name = resume_data.get('filename', 'resume.pdf')
            
            if not content:
                logger.warning("No resume content provided")
                return None
            
            # Determine file extension
            _, ext = os.path.splitext(file_name)
            if not ext:
                ext = '.pdf'  # Default extension
            
            # Create target directory
            storage_path = Path(RECRUITMENT_SETTINGS['resume_storage_path'])
            target_dir = storage_path / application_id
            os.makedirs(target_dir, exist_ok=True)
            
            # Save file
            file_path = target_dir / f"resume{ext}"
            
            # Convert content if needed
            if isinstance(content, str):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                with open(file_path, 'wb') as f:
                    f.write(content)
            
            # Return relative path
            return str(file_path.relative_to(storage_path))
            
        except Exception as e:
            logger.error(f"Error saving resume: {e}")
            return None
    
    def update_application_stage(self, application_id: str, 
                               new_stage: str, comments: str = "") -> bool:
        """
        Update application stage
        
        Args:
            application_id: Application ID
            new_stage: New recruitment stage
            comments: Optional comments
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            # Validate stage
            if new_stage not in RECRUITMENT_SETTINGS['stages']:
                logger.error(f"Invalid recruitment stage: {new_stage}")
                return False
            
            cursor = conn.cursor()
            
            # Update application stage
            query = """
                UPDATE hr_job_applications
                SET current_stage = %s, last_modified = NOW()
                WHERE application_id = %s
            """
            
            cursor.execute(query, (new_stage, application_id))
            
            # Record stage change
            log_query = """
                INSERT INTO hr_application_stage_log (
                    application_id, stage, change_date, comments
                ) VALUES (%s, %s, NOW(), %s)
            """
            
            cursor.execute(log_query, (application_id, new_stage, comments))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Updated application {application_id} stage to {new_stage}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating application {application_id} stage: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return False
    
    def schedule_interview(self, application_id: str, interview_data: Dict[str, Any]) -> Optional[str]:
        """
        Schedule interview for an application
        
        Args:
            application_id: Application ID
            interview_data: Interview details
            
        Returns:
            Interview ID if successful, None otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return None
            
            cursor = conn.cursor()
            
            # Generate interview ID
            interview_id = f"INT-{uuid.uuid4().hex[:8].upper()}"
            
            # Extract interview information
            interview_type = interview_data.get('type', 'Technical')
            interviewers = interview_data.get('interviewers', [])
            location = interview_data.get('location', 'Online')
            interview_date = interview_data.get('date')
            start_time = interview_data.get('start_time')
            end_time = interview_data.get('end_time')
            notes = interview_data.get('notes', '')
            
            # Insert interview record
            query = """
                INSERT INTO hr_interviews (
                    interview_id, application_id, interview_type,
                    location, interview_date, start_time, end_time,
                    notes, status
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            cursor.execute(query, (
                interview_id, application_id, interview_type,
                location, interview_date, start_time, end_time,
                notes, 'Scheduled'
            ))
            
            # Store interviewers
            if interviewers:
                for interviewer in interviewers:
                    int_query = """
                        INSERT INTO hr_interview_panel (
                            interview_id, interviewer_name, interviewer_email,
                            interviewer_role
                        ) VALUES (%s, %s, %s, %s)
                    """
                    
                    cursor.execute(int_query, (
                        interview_id,
                        interviewer.get('name', ''),
                        interviewer.get('email', ''),
                        interviewer.get('role', '')
                    ))
            
            # Update application stage to appropriate interview stage
            stages = RECRUITMENT_SETTINGS['stages']
            current_stage_query = """
                SELECT current_stage FROM hr_job_applications
                WHERE application_id = %s
            """
            
            cursor.execute(current_stage_query, (application_id,))
            current_stage = cursor.fetchone()[0] if cursor.fetchone() else None
            
            # Find appropriate interview stage
            interview_stages = [s for s in stages if 'interview' in s.lower()]
            
            if interview_stages and current_stage:
                # Get the next interview stage based on current stage
                current_index = stages.index(current_stage) if current_stage in stages else -1
                
                next_stage = None
                for stage in interview_stages:
                    stage_index = stages.index(stage)
                    if stage_index > current_index:
                        next_stage = stage
                        break
                
                if next_stage:
                    stage_query = """
                        UPDATE hr_job_applications
                        SET current_stage = %s, last_modified = NOW()
                        WHERE application_id = %s
                    """
                    
                    cursor.execute(stage_query, (next_stage, application_id))
                    
                    # Record stage change
                    log_query = """
                        INSERT INTO hr_application_stage_log (
                            application_id, stage, change_date, comments
                        ) VALUES (%s, %s, NOW(), %s)
                    """
                    
                    cursor.execute(log_query, (
                        application_id, next_stage, 
                        f"Interview scheduled: {interview_id}"
                    ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Scheduled interview {interview_id} for application {application_id}")
            return interview_id
            
        except Exception as e:
            logger.error(f"Error scheduling interview for {application_id}: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return None
    
    def record_interview_feedback(self, interview_id: str, feedback_data: Dict[str, Any]) -> bool:
        """
        Record interview feedback
        
        Args:
            interview_id: Interview ID
            feedback_data: Feedback details
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor()
            
            # Extract feedback information
            interviewer_name = feedback_data.get('interviewer_name', '')
            comments = feedback_data.get('comments', '')
            recommendation = feedback_data.get('recommendation', 'No Decision')
            skills_rating = feedback_data.get('skills_rating', {})
            
            # Insert feedback record
            query = """
                INSERT INTO hr_interview_feedback (
                    interview_id, interviewer_name, comments,
                    recommendation, skills_rating, feedback_date
                ) VALUES (
                    %s, %s, %s, %s, %s, NOW()
                )
            """
            
            cursor.execute(query, (
                interview_id, interviewer_name, comments,
                recommendation, json.dumps(skills_rating)
            ))
            
            # Update interview status
            status_query = """
                UPDATE hr_interviews
                SET status = 'Completed'
                WHERE interview_id = %s
            """
            
            cursor.execute(status_query, (interview_id,))
            
            # Check if this is the final feedback for this interview
            check_query = """
                SELECT COUNT(*) AS feedback_count, COUNT(DISTINCT ip.interviewer_name) AS interviewer_count
                FROM hr_interview_panel ip
                LEFT JOIN hr_interview_feedback if ON ip.interview_id = if.interview_id 
                    AND ip.interviewer_name = if.interviewer_name
                WHERE ip.interview_id = %s
            """
            
            cursor.execute(check_query, (interview_id,))
            counts = cursor.fetchone()
            
            if counts and counts[0] == counts[1]:
                # All interviewers have provided feedback
                # Get application_id for this interview
                app_query = """
                    SELECT application_id FROM hr_interviews
                    WHERE interview_id = %s
                """
                
                cursor.execute(app_query, (interview_id,))
                app_result = cursor.fetchone()
                
                if app_result:
                    application_id = app_result[0]
                    
                    # Check if positive recommendations
                    pos_query = """
                        SELECT COUNT(*) AS total, 
                            SUM(CASE WHEN recommendation = 'Move Forward' THEN 1 ELSE 0 END) AS positive
                        FROM hr_interview_feedback
                        WHERE interview_id = %s
                    """
                    
                    cursor.execute(pos_query, (interview_id,))
                    rec_counts = cursor.fetchone()
                    
                    if rec_counts and rec_counts[0] > 0:
                        # Decide next stage based on feedback
                        if rec_counts[1] / rec_counts[0] >= 0.5:  # More than 50% positive
                            # Move to next stage
                            self._move_to_next_stage(cursor, application_id)
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Recorded feedback for interview {interview_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording feedback for {interview_id}: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return False
    
    def _move_to_next_stage(self, cursor, application_id: str) -> None:
        """
        Move application to next stage
        
        Args:
            cursor: Database cursor
            application_id: Application ID
        """
        # Get current stage
        stage_query = """
            SELECT current_stage FROM hr_job_applications
            WHERE application_id = %s
        """
        
        cursor.execute(stage_query, (application_id,))
        result = cursor.fetchone()
        
        if not result:
            return
            
        current_stage = result[0]
        
        # Get next stage
        stages = RECRUITMENT_SETTINGS['stages']
        
        try:
            current_index = stages.index(current_stage)
            if current_index < len(stages) - 1:
                next_stage = stages[current_index + 1]
                
                # Update stage
                update_query = """
                    UPDATE hr_job_applications
                    SET current_stage = %s, last_modified = NOW()
                    WHERE application_id = %s
                """
                
                cursor.execute(update_query, (next_stage, application_id))
                
                # Record stage change
                log_query = """
                    INSERT INTO hr_application_stage_log (
                        application_id, stage, change_date, comments
                    ) VALUES (%s, %s, NOW(), %s)
                """
                
                cursor.execute(log_query, (
                    application_id, next_stage, 
                    "Moved to next stage based on positive interview feedback"
                ))
                
        except ValueError:
            logger.warning(f"Current stage {current_stage} not found in configured stages")
    
    def search_applications(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search job applications
        
        Args:
            criteria: Search criteria
            
        Returns:
            List of matching applications
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            # Build WHERE conditions based on criteria
            conditions = []
            params = []
            
            if 'job_id' in criteria:
                conditions.append("a.job_id = %s")
                params.append(criteria['job_id'])
            
            if 'candidate_name' in criteria:
                conditions.append("a.candidate_name LIKE %s")
                params.append(f"%{criteria['candidate_name']}%")
            
            if 'stage' in criteria:
                conditions.append("a.current_stage = %s")
                params.append(criteria['stage'])
            
            if 'status' in criteria:
                conditions.append("a.status = %s")
                params.append(criteria['status'])
            
            if 'date_from' in criteria:
                conditions.append("a.application_date >= %s")
                params.append(criteria['date_from'])
            
            if 'date_to' in criteria:
                conditions.append("a.application_date <= %s")
                params.append(criteria['date_to'])
            
            # Build the full query
            query = """
                SELECT a.*, j.title AS job_title, j.department
                FROM hr_job_applications a
                JOIN hr_job_openings j ON a.job_id = j.job_id
            """
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            # Add order by
            query += " ORDER BY a.application_date DESC"
            
            # Add limit if specified
            if 'limit' in criteria:
                query += " LIMIT %s"
                params.append(criteria['limit'])
            else:
                # Default limit
                query += " LIMIT 50"
            
            # Execute the query
            cursor.execute(query, params)
            applications = cursor.fetchall()
            cursor.close()
            
            return applications
            
        except Exception as e:
            logger.error(f"Error searching applications: {e}")
            return []
    
    def create_offer(self, application_id: str, offer_data: Dict[str, Any]) -> Optional[str]:
        """
        Create job offer
        
        Args:
            application_id: Application ID
            offer_data: Offer details
            
        Returns:
            Offer ID if successful, None otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return None
            
            cursor = conn.cursor()
            
            # Generate offer ID
            offer_id = f"OFFER-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            # Extract offer information
            position = offer_data.get('position', '')
            department = offer_data.get('department', '')
            salary = offer_data.get('salary', 0)
            joining_date = offer_data.get('joining_date')
            expiry_date = offer_data.get('expiry_date')
            probation_period = offer_data.get('probation_period', 
                                             RECRUITMENT_SETTINGS['default_probation_period_months'])
            benefits = offer_data.get('benefits', {})
            additional_terms = offer_data.get('additional_terms', '')
            
            # Get job_id from application
            job_query = """
                SELECT job_id FROM hr_job_applications
                WHERE application_id = %s
            """
            
            cursor.execute(job_query, (application_id,))
            job_result = cursor.fetchone()
            job_id = job_result[0] if job_result else None
            
            # Insert offer record
            query = """
                INSERT INTO hr_job_offers (
                    offer_id, application_id, job_id, position,
                    department, salary, joining_date, expiry_date,
                    probation_period, benefits, additional_terms,
                    created_date, status
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s
                )
            """
            
            cursor.execute(query, (
                offer_id, application_id, job_id, position,
                department, salary, joining_date, expiry_date,
                probation_period, json.dumps(benefits), additional_terms,
                'Created'
            ))
            
            # Update application stage to Offer
            stages = RECRUITMENT_SETTINGS['stages']
            offer_stage = 'Offer'
            
            if offer_stage in stages:
                stage_query = """
                    UPDATE hr_job_applications
                    SET current_stage = %s, last_modified = NOW()
                    WHERE application_id = %s
                """
                
                cursor.execute(stage_query, (offer_stage, application_id))
                
                # Record stage change
                log_query = """
                    INSERT INTO hr_application_stage_log (
                        application_id, stage, change_date, comments
                    ) VALUES (%s, %s, NOW(), %s)
                """
                
                cursor.execute(log_query, (
                    application_id, offer_stage, f"Offer created: {offer_id}"
                ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Created offer {offer_id} for application {application_id}")
            return offer_id
            
        except Exception as e:
            logger.error(f"Error creating offer for {application_id}: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return None
    
    def update_offer_status(self, offer_id: str, status: str, comments: str = "") -> bool:
        """
        Update offer status
        
        Args:
            offer_id: Offer ID
            status: New status (e.g., 'Sent', 'Accepted', 'Rejected')
            comments: Optional comments
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor()
            
            # Update offer status
            query = """
                UPDATE hr_job_offers
                SET status = %s, last_modified = NOW()
                WHERE offer_id = %s
            """
            
            cursor.execute(query, (status, offer_id))
            
            # Record status change
            log_query = """
                INSERT INTO hr_offer_status_log (
                    offer_id, status, change_date, comments
                ) VALUES (%s, %s, NOW(), %s)
            """
            
            cursor.execute(log_query, (offer_id, status, comments))
            
            # If offer is accepted, update application stage to Onboarding
            if status == 'Accepted':
                # Get application_id for this offer
                app_query = """
                    SELECT application_id FROM hr_job_offers
                    WHERE offer_id = %s
                """
                
                cursor.execute(app_query, (offer_id,))
                app_result = cursor.fetchone()
                
                if app_result:
                    application_id = app_result[0]
                    
                    # Check if Onboarding stage exists
                    stages = RECRUITMENT_SETTINGS['stages']
                    onboarding_stage = 'Onboarding'
                    
                    if onboarding_stage in stages:
                        stage_query = """
                            UPDATE hr_job_applications
                            SET current_stage = %s, last_modified = NOW()
                            WHERE application_id = %s
                        """
                        
                        cursor.execute(stage_query, (onboarding_stage, application_id))
                        
                        # Record stage change
                        log_query = """
                            INSERT INTO hr_application_stage_log (
                                application_id, stage, change_date, comments
                            ) VALUES (%s, %s, NOW(), %s)
                        """
                        
                        cursor.execute(log_query, (
                            application_id, onboarding_stage, "Offer accepted, moving to onboarding"
                        ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Updated offer {offer_id} status to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating offer {offer_id} status: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return False
    
    def start_onboarding(self, application_id: str) -> Optional[str]:
        """
        Start onboarding process
        
        Args:
            application_id: Application ID
            
        Returns:
            Onboarding ID if successful, None otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return None
            
            cursor = conn.cursor()
            
            # Get offer details
            offer_query = """
                SELECT o.*, a.candidate_name, a.email, a.phone
                FROM hr_job_offers o
                JOIN hr_job_applications a ON o.application_id = a.application_id
                WHERE o.application_id = %s AND o.status = 'Accepted'
            """
            
            cursor.execute(offer_query, (application_id,))
            offer = cursor.fetchone()
            
            if not offer:
                logger.warning(f"No accepted offer found for application {application_id}")
                return None
            
            # Generate onboarding ID
            onboarding_id = f"ONB-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            # Insert onboarding record
            query = """
                INSERT INTO hr_onboarding (
                    onboarding_id, application_id, candidate_name,
                    position, department, joining_date,
                    start_date, status
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, NOW(), %s
                )
            """
            
            cursor.execute(query, (
                onboarding_id, application_id, offer[2],  # candidate_name
                offer['position'], offer['department'], offer['joining_date'],
                'In Progress'
            ))
            
            # Create default onboarding tasks
            default_tasks = [
                {'name': 'HR Documentation', 'category': 'Paperwork'},
                {'name': 'Banking Details Setup', 'category': 'Paperwork'},
                {'name': 'ID Card Creation', 'category': 'Access'},
                {'name': 'Email Setup', 'category': 'IT'},
                {'name': 'System Access', 'category': 'IT'},
                {'name': 'Department Introduction', 'category': 'Introduction'}
            ]
            
            for task in default_tasks:
                task_query = """
                    INSERT INTO hr_onboarding_tasks (
                        onboarding_id, task_name, category,
                        due_date, status
                    ) VALUES (%s, %s, %s, %s, %s)
                """
                
                # Due date is joining date + 2 days
                due_date = datetime.datetime.strptime(
                    offer['joining_date'], '%Y-%m-%d'
                ) + datetime.timedelta(days=2)
                
                cursor.execute(task_query, (
                    onboarding_id, task['name'], task['category'],
                    due_date.strftime('%Y-%m-%d'), 'Pending'
                ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Started onboarding {onboarding_id} for application {application_id}")
            return onboarding_id
            
        except Exception as e:
            logger.error(f"Error starting onboarding for {application_id}: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return None
    
    def get_recruitment_metrics(self) -> Dict[str, Any]:
        """
        Get recruitment metrics
        
        Returns:
            Recruitment metrics data
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return {}
            
            cursor = conn.cursor(dictionary=True)
            
            # Time period - last 90 days
            start_date = (datetime.datetime.now() - datetime.timedelta(days=90)).strftime('%Y-%m-%d')
            
            # Get application counts by stage
            stage_query = """
                SELECT current_stage AS stage, COUNT(*) AS count
                FROM hr_job_applications
                WHERE application_date >= %s
                GROUP BY current_stage
            """
            
            cursor.execute(stage_query, (start_date,))
            stage_counts = cursor.fetchall()
            
            # Get job opening stats
            job_query = """
                SELECT status, COUNT(*) AS count
                FROM hr_job_openings
                WHERE posting_date >= %s OR status = 'Open'
                GROUP BY status
            """
            
            cursor.execute(job_query, (start_date,))
            job_counts = cursor.fetchall()
            
            # Get offer conversion rate
            offer_query = """
                SELECT 
                    COUNT(*) AS total_offers,
                    SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) AS accepted,
                    SUM(CASE WHEN status = 'Rejected' THEN 1 ELSE 0 END) AS rejected
                FROM hr_job_offers
                WHERE created_date >= %s
            """
            
            cursor.execute(offer_query, (start_date,))
            offer_stats = cursor.fetchone()
            
            # Get time-to-fill stats
            ttf_query = """
                SELECT AVG(DATEDIFF(o.joining_date, j.posting_date)) AS avg_days_to_fill
                FROM hr_job_offers o
                JOIN hr_job_applications a ON o.application_id = a.application_id
                JOIN hr_job_openings j ON a.job_id = j.job_id
                WHERE o.status = 'Accepted'
                AND j.posting_date >= %s
            """
            
            cursor.execute(ttf_query, (start_date,))
            ttf_stats = cursor.fetchone()
            
            cursor.close()
            
            # Compile metrics
            metrics = {
                'period': f"Last 90 days (since {start_date})",
                'applications_by_stage': stage_counts,
                'job_openings_by_status': job_counts,
                'offer_stats': {
                    'total': offer_stats['total_offers'] if offer_stats else 0,
                    'accepted': offer_stats['accepted'] if offer_stats else 0,
                    'rejected': offer_stats['rejected'] if offer_stats else 0,
                    'conversion_rate': (
                        round(offer_stats['accepted'] / offer_stats['total_offers'] * 100, 2)
                        if offer_stats and offer_stats['total_offers'] > 0 else 0
                    )
                },
                'avg_days_to_fill': ttf_stats['avg_days_to_fill'] if ttf_stats and ttf_stats['avg_days_to_fill'] else 0
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting recruitment metrics: {e}")
            return {}


# Singleton instance
recruitment_manager = RecruitmentManager()


def get_recruitment_manager() -> RecruitmentManager:
    """Get the recruitment manager instance"""
    return recruitment_manager
