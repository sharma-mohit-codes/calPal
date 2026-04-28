/**
 * Utility functions for formatting dates, times, and text
 */

export const formatDate = (dateString) => {
    const date = new Date(dateString);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
  
    // Check if today
    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    }
    
    // Check if tomorrow
    if (date.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow';
    }
  
    // Format as "Mon, Jan 15"
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric' 
    });
  };
  
  export const formatTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    });
  };
  
  export const formatDateTime = (dateString) => {
    return `${formatDate(dateString)} at ${formatTime(dateString)}`;
  };
  
  export const formatEventsList = (events) => {
    if (!events || events.length === 0) {
      return 'No upcoming events';
    }
  
    return events.map((event, idx) => {
      const start = event.start?.dateTime || event.start?.date;
      return `${idx + 1}. ${event.summary} - ${formatDateTime(start)}`;
    }).join('\n');
  };
  
  export const capitalizeFirst = (str) => {
    return str.charAt(0).toUpperCase() + str.slice(1);
  };
  
  export const truncate = (str, maxLength = 50) => {
    if (str.length <= maxLength) return str;
    return str.substring(0, maxLength) + '...';
  };