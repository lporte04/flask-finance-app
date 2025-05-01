from flask import flash
from wtforms.fields import FieldList

def flash_form_errors(form):
    """Extract and flash form errors in a user-friendly way."""
    
    # Handle top-level form fields
    for field_name, errors in form.errors.items():
        if field_name not in form._fields:
            # Skip special fields
            continue
            
        field = form._fields[field_name]
        
        # Handle nested forms (FieldList)
        if isinstance(field, FieldList):
            for i, entry in enumerate(field.entries):
                for subfield, suberrors in entry.form.errors.items():
                    # Get readable names
                    parent_name = field.label.text
                    if hasattr(entry.form[subfield], 'label'):
                        child_name = entry.form[subfield].label.text
                    else:
                        child_name = subfield.capitalize()
                    
                    # Format error (e.g., "Spending #1 Amount: Must be positive")
                    for error in suberrors:
                        flash(f"{parent_name} #{i+1} {child_name}: {error}", "danger")
        else:
            # Regular field errors
            field_label = field.label.text
            for error in errors:
                flash(f"{field_label}: {error}", "danger")