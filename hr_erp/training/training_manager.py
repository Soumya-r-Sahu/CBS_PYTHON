"""
Training Manager module for managing all training-related operations.
"""

import datetime
from typing import Dict, List, Optional, Union
import logging


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
logger = logging.getLogger(__name__)

class TrainingProgram:
    """Class representing a training program"""
    
    def __init__(self, program_id: str, name: str, description: str,
                 start_date: datetime.date, end_date: datetime.date,
                 instructor: str, capacity: int, prerequisites: List[str] = None):
        """
        Initialize a training program.
        
        Args:
            program_id: Unique identifier for the training program
            name: Name of the training program
            description: Detailed description of what the program covers
            start_date: Start date of the program
            end_date: End date of the program
            instructor: Name of the program instructor
            capacity: Maximum number of participants
            prerequisites: List of prerequisite skills or courses
        """
        self.program_id = program_id
        self.name = name
        self.description = description
        self.start_date = start_date
        self.end_date = end_date
        self.instructor = instructor
        self.capacity = capacity
        self.prerequisites = prerequisites or []
        self.participants = []
        self.status = "Scheduled"
        
    def add_participant(self, employee_id: str) -> bool:
        """
        Add a participant to the training program.
        
        Args:
            employee_id: Employee ID to add to the program
            
        Returns:
            bool: True if added successfully, False otherwise
        """
        if len(self.participants) >= self.capacity:
            logger.warning(f"Training program {self.program_id} is at full capacity")
            return False
            
        if employee_id in self.participants:
            logger.warning(f"Employee {employee_id} already enrolled in program {self.program_id}")
            return False
            
        self.participants.append(employee_id)
        logger.info(f"Employee {employee_id} added to training program {self.program_id}")
        return True
        
    def remove_participant(self, employee_id: str) -> bool:
        """
        Remove a participant from the training program.
        
        Args:
            employee_id: Employee ID to remove from the program
            
        Returns:
            bool: True if removed successfully, False if employee not found
        """
        if employee_id not in self.participants:
            logger.warning(f"Employee {employee_id} not enrolled in program {self.program_id}")
            return False
            
        self.participants.remove(employee_id)
        logger.info(f"Employee {employee_id} removed from training program {self.program_id}")
        return True
        
    def update_status(self, status: str) -> None:
        """
        Update the status of the training program.
        
        Args:
            status: New status for the program (e.g., "Scheduled", "In Progress", "Completed", "Cancelled")
        """
        valid_statuses = ["Scheduled", "In Progress", "Completed", "Cancelled"]
        if status not in valid_statuses:
            logger.error(f"Invalid status {status} for training program")
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
            
        self.status = status
        logger.info(f"Training program {self.program_id} status updated to {status}")


class TrainingRecord:
    """Class representing an employee's training record"""
    
    def __init__(self, employee_id: str, program_id: str, 
                 completion_date: Optional[datetime.date] = None,
                 performance_score: Optional[float] = None,
                 certification_earned: Optional[str] = None):
        """
        Initialize a training record.
        
        Args:
            employee_id: ID of the employee
            program_id: ID of the training program
            completion_date: Date when the training was completed
            performance_score: Score achieved in the training
            certification_earned: Certification earned from the training
        """
        self.employee_id = employee_id
        self.program_id = program_id
        self.registration_date = datetime.date.today()
        self.completion_date = completion_date
        self.performance_score = performance_score
        self.certification_earned = certification_earned
        self.feedback = ""
        
    def add_feedback(self, feedback: str) -> None:
        """Add feedback to the training record"""
        self.feedback = feedback
        
    def mark_completed(self, completion_date: datetime.date, 
                       performance_score: float = None,
                       certification_earned: str = None) -> None:
        """
        Mark the training as completed.
        
        Args:
            completion_date: Date of completion
            performance_score: Score achieved (optional)
            certification_earned: Certification earned (optional)
        """
        self.completion_date = completion_date
        self.performance_score = performance_score
        self.certification_earned = certification_earned


class TrainingManager:
    """Manager class for handling all training-related operations"""
    
    def __init__(self):
        """Initialize the training manager"""
        self.training_programs = {}  # Dictionary to store training programs
        self.training_records = {}   # Dictionary to store training records
        logger.info("Training Manager initialized")
        
    def create_training_program(self, program_id: str, name: str, description: str,
                               start_date: Union[datetime.date, str], 
                               end_date: Union[datetime.date, str],
                               instructor: str, capacity: int, 
                               prerequisites: List[str] = None) -> TrainingProgram:
        """
        Create a new training program.
        
        Args:
            program_id: Unique identifier for the training program
            name: Name of the training program
            description: Detailed description of what the program covers
            start_date: Start date of the program (datetime.date or string in 'YYYY-MM-DD' format)
            end_date: End date of the program (datetime.date or string in 'YYYY-MM-DD' format)
            instructor: Name of the program instructor
            capacity: Maximum number of participants
            prerequisites: List of prerequisite skills or courses
            
        Returns:
            TrainingProgram: The created training program
        """
        # Convert string dates to datetime objects if needed
        if isinstance(start_date, str):
            start_date = datetime.date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.date.fromisoformat(end_date)
            
        if program_id in self.training_programs:
            logger.error(f"Training program with ID {program_id} already exists")
            raise ValueError(f"Training program with ID {program_id} already exists")
            
        program = TrainingProgram(
            program_id=program_id,
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            instructor=instructor,
            capacity=capacity,
            prerequisites=prerequisites
        )
        
        self.training_programs[program_id] = program
        logger.info(f"Created new training program: {name} ({program_id})")
        return program
        
    def get_training_program(self, program_id: str) -> Optional[TrainingProgram]:
        """
        Get a training program by its ID.
        
        Args:
            program_id: ID of the training program to retrieve
            
        Returns:
            TrainingProgram: The training program or None if not found
        """
        program = self.training_programs.get(program_id)
        if not program:
            logger.warning(f"Training program {program_id} not found")
        return program
        
    def update_training_program(self, program_id: str, **kwargs) -> bool:
        """
        Update a training program's details.
        
        Args:
            program_id: ID of the training program to update
            **kwargs: Fields to update and their new values
            
        Returns:
            bool: True if updated successfully, False if program not found
        """
        program = self.get_training_program(program_id)
        if not program:
            return False
            
        # Update the attributes provided in kwargs
        for key, value in kwargs.items():
            if hasattr(program, key):
                setattr(program, key, value)
                
        logger.info(f"Updated training program {program_id}")
        return True
        
    def delete_training_program(self, program_id: str) -> bool:
        """
        Delete a training program.
        
        Args:
            program_id: ID of the training program to delete
            
        Returns:
            bool: True if deleted successfully, False if not found
        """
        if program_id not in self.training_programs:
            logger.warning(f"Training program {program_id} not found for deletion")
            return False
            
        del self.training_programs[program_id]
        logger.info(f"Deleted training program {program_id}")
        return True
        
    def register_employee_for_training(self, employee_id: str, program_id: str) -> bool:
        """
        Register an employee for a training program.
        
        Args:
            employee_id: ID of the employee
            program_id: ID of the training program
            
        Returns:
            bool: True if registered successfully, False otherwise
        """
        program = self.get_training_program(program_id)
        if not program:
            return False
            
        # Try to add the participant to the program
        if not program.add_participant(employee_id):
            return False
            
        # Create a training record
        record_id = f"{employee_id}_{program_id}"
        record = TrainingRecord(employee_id=employee_id, program_id=program_id)
        self.training_records[record_id] = record
        
        logger.info(f"Employee {employee_id} registered for training program {program_id}")
        return True
        
    def complete_employee_training(self, employee_id: str, program_id: str, 
                                  completion_date: Union[datetime.date, str],
                                  performance_score: float = None,
                                  certification_earned: str = None) -> bool:
        """
        Mark an employee's training as completed.
        
        Args:
            employee_id: ID of the employee
            program_id: ID of the training program
            completion_date: Date of completion
            performance_score: Score achieved (optional)
            certification_earned: Certification earned (optional)
            
        Returns:
            bool: True if marked as completed successfully, False otherwise
        """
        # Convert string date to datetime object if needed
        if isinstance(completion_date, str):
            completion_date = datetime.date.fromisoformat(completion_date)
            
        record_id = f"{employee_id}_{program_id}"
        if record_id not in self.training_records:
            logger.warning(f"No training record found for employee {employee_id} in program {program_id}")
            return False
            
        record = self.training_records[record_id]
        record.mark_completed(
            completion_date=completion_date,
            performance_score=performance_score,
            certification_earned=certification_earned
        )
        
        logger.info(f"Training completed for employee {employee_id} in program {program_id}")
        return True
        
    def get_employee_training_history(self, employee_id: str) -> List[Dict]:
        """
        Get the training history of an employee.
        
        Args:
            employee_id: ID of the employee
            
        Returns:
            list: List of training records for the employee
        """
        history = []
        for record_id, record in self.training_records.items():
            if record.employee_id == employee_id:
                program = self.get_training_program(record.program_id)
                if program:
                    history.append({
                        "program_id": record.program_id,
                        "program_name": program.name,
                        "registration_date": record.registration_date,
                        "completion_date": record.completion_date,
                        "performance_score": record.performance_score,
                        "certification_earned": record.certification_earned
                    })
                    
        return history
        
    def get_program_participants(self, program_id: str) -> List[str]:
        """
        Get the list of participants in a training program.
        
        Args:
            program_id: ID of the training program
            
        Returns:
            list: List of employee IDs enrolled in the program
        """
        program = self.get_training_program(program_id)
        if not program:
            return []
            
        return program.participants.copy()
        
    def generate_training_report(self, from_date: Optional[datetime.date] = None, 
                                to_date: Optional[datetime.date] = None) -> Dict:
        """
        Generate a report of training activities.
        
        Args:
            from_date: Start date for the report period (optional)
            to_date: End date for the report period (optional)
            
        Returns:
            dict: Report containing training statistics
        """
        if not from_date:
            from_date = datetime.date.min
        if not to_date:
            to_date = datetime.date.max
            
        total_programs = 0
        active_programs = 0
        completed_programs = 0
        total_participants = 0
        avg_performance = 0.0
        performance_scores = []
        
        for program in self.training_programs.values():
            if from_date <= program.start_date <= to_date or from_date <= program.end_date <= to_date:
                total_programs += 1
                total_participants += len(program.participants)
                
                if program.status == "In Progress":
                    active_programs += 1
                elif program.status == "Completed":
                    completed_programs += 1
        
        # Calculate average performance if there are completed trainings
        for record in self.training_records.values():
            if record.performance_score is not None and record.completion_date and from_date <= record.completion_date <= to_date:
                performance_scores.append(record.performance_score)
                
        if performance_scores:
            avg_performance = sum(performance_scores) / len(performance_scores)
            
        return {
            "report_period": {
                "from_date": from_date.isoformat(),
                "to_date": to_date.isoformat()
            },
            "total_programs": total_programs,
            "active_programs": active_programs,
            "completed_programs": completed_programs,
            "total_participants": total_participants,
            "average_performance_score": round(avg_performance, 2)
        }
