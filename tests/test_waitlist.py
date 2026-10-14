from datetime import datetime, timedelta
import pytest
from src.waitlist import AppointmentWaitlist

def test_fifo_order_within_same_priority():
    waitlist = AppointmentWaitlist()
    waitlist.add_student("Alice", priority=1)
    waitlist.add_student("Bob", priority=1)
    
    # FIFO means Alice came first, so she should be served first
    assert waitlist.get_next_eligible_student() == "Alice"
    assert waitlist.get_next_eligible_student() == "Bob"

def test_priority_takes_precedence_over_fifo():
    waitlist = AppointmentWaitlist()
    waitlist.add_student("Charlie", priority=2)
    waitlist.add_student("Diana", priority=1) # Higher priority (1 < 2)
    
    # Diana has higher priority despite arriving second
    assert waitlist.get_next_eligible_student() == "Diana"
    assert waitlist.get_next_eligible_student() == "Charlie"

def test_withdrawal():
    waitlist = AppointmentWaitlist()
    waitlist.add_student("Evan", priority=1)
    waitlist.add_student("Fiona", priority=1)
    
    # Evan withdraws
    assert waitlist.withdraw_student("Evan") is True
    
    # Fiona should be served next since Evan is withdrawn
    assert waitlist.get_next_eligible_student() == "Fiona"
    assert waitlist.get_next_eligible_student() is None

def test_expiry():
    waitlist = AppointmentWaitlist()
    old_time = datetime.now() - timedelta(seconds=120)
    
    # Manually insert an old entry to test expiration
    entry = waitlist.add_student("George", priority=1)
    entry.timestamp = old_time
    
    expired = waitlist.remove_expired_requests(max_age_seconds=60)
    assert "George" in expired
    
    # Expired student shouldn't be served
    assert waitlist.get_next_eligible_student() is None