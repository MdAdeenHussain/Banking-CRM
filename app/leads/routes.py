"""
app/leads/routes.py
Lead management routes (CRUD, assignment, status changes).
"""

from flask import request, jsonify, g, render_template, redirect, url_for, flash
from app.leads import leads_bp
from app.leads.services import LeadService
from app.decorators import login_required, tenant_required, role_required
from app.constants import UserRole
from app.errors import NotFoundError, ValidationError
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# LEAD LIST & PAGINATION
# ============================================================================

@leads_bp.route("", methods=["GET"])
@login_required
@tenant_required
def list_leads():
    """GET /leads - List all leads for tenant with filters."""
    try:
        tenant_id = g.current_user.tenant_id
        
        # Get filters from query params
        status = request.args.get("status")
        source = request.args.get("source")
        city = request.args.get("city")
        page = request.args.get("page", 1, type=int)
        limit = 20
        skip = (page - 1) * limit
        
        # Build filters dict
        filters = {}
        if status:
            filters["status"] = status
        if source:
            filters["source"] = source
        if city:
            filters["city"] = city
        
        # Get leads from service
        result = LeadService.get_leads(tenant_id, filters=filters, skip=skip, limit=limit)
        
        # Convert leads to list (they come as list from service)
        leads = result["items"]
        total_pages = (result["total"] + limit - 1) // limit
        
        return render_template(
            "leads/list.html",
            leads=leads,
            page=page,
            total_pages=total_pages,
            status_filter=status,
            source_filter=source,
            city_filter=city
        )
    
    except Exception as e:
        logger.error(f"Error listing leads: {str(e)}")
        flash("Error loading leads", "error")
        return render_template("leads/list.html", leads=[], page=1, total_pages=1)


# ============================================================================
# LEAD CREATION
# ============================================================================

@leads_bp.route("/create", methods=["GET", "POST"])
@login_required
@tenant_required
def create_lead():
    """GET /leads/create - Display lead creation form."""
    """POST /leads/create - Create new lead."""
    
    # Handle GET - show form
    if request.method == "GET":
        return render_template("leads/form.html", lead=None)
    
    # Handle POST - create lead
    try:
        tenant_id = g.current_user.tenant_id
        user_id = g.current_user.id
        
        # Extract form data
        name = request.form.get("name", "").strip()
        mobile = request.form.get("mobile", "").strip()
        email = request.form.get("email", "").strip()
        loan_type = request.form.get("loan_type", "").strip()
        loan_amount = request.form.get("loan_amount", "").strip()
        source = request.form.get("source", "").strip()
        city = request.form.get("city", "").strip()
        priority = request.form.get("priority", "MEDIUM").strip()
        notes = request.form.get("notes", "").strip()
        
        # Validate required fields
        errors = []
        if not name:
            errors.append("Name is required")
        if not mobile:
            errors.append("Mobile number is required")
        if not loan_type:
            errors.append("Loan type is required")
        
        if errors:
            return render_template("leads/form.html", lead=None, errors=errors), 400
        
        # Convert loan_amount to float
        try:
            loan_amount = float(loan_amount) if loan_amount else None
        except ValueError:
            return render_template(
                "leads/form.html",
                lead=None,
                errors=["Invalid loan amount format"]
            ), 400
        
        # Create custom_data with notes
        custom_data = {}
        if notes:
            custom_data["notes"] = notes
        
        # Call service to create lead
        lead_data = LeadService.create_lead(
            tenant_id=tenant_id,
            name=name,
            mobile=mobile,
            email=email if email else None,
            loan_type=loan_type,
            loan_amount=loan_amount,
            source=source if source else None,
            city=city if city else None,
            priority=priority,
            custom_data=custom_data if custom_data else None,
            created_by_id=user_id
        )
        
        flash("Lead created successfully", "success")
        return redirect(url_for("leads.view_lead", lead_id=lead_data["id"]))
    
    except ValidationError as e:
        logger.warning(f"Validation error creating lead: {str(e)}")
        return render_template(
            "leads/form.html",
            lead=None,
            errors=[str(e)]
        ), 400
    except Exception as e:
        logger.error(f"Error creating lead: {str(e)}")
        flash("Error creating lead", "error")
        return redirect(url_for("leads.list_leads"))


# ============================================================================
# LEAD DETAIL & VIEW
# ============================================================================

@leads_bp.route("/<lead_id>", methods=["GET"])
@login_required
@tenant_required
def view_lead(lead_id):
    """GET /leads/<uuid> - Get single lead details."""
    try:
        tenant_id = g.current_user.tenant_id
        
        # Fetch lead with notes, assignments, history
        lead_data = LeadService.get_lead(tenant_id, lead_id)
        
        # Render a detail view template
        return render_template("leads/detail.html", lead=lead_data)
    
    except NotFoundError:
        flash("Lead not found", "error")
        return redirect(url_for("leads.list_leads"))
    except Exception as e:
        logger.error(f"Error fetching lead: {str(e)}")
        flash("Error loading lead", "error")
        return redirect(url_for("leads.list_leads"))


# ============================================================================
# LEAD EDIT & UPDATE
# ============================================================================

@leads_bp.route("/<lead_id>/edit", methods=["GET"])
@login_required
@tenant_required
def edit_lead(lead_id):
    """GET /leads/<uuid>/edit - Display edit form."""
    try:
        tenant_id = g.current_user.tenant_id
        lead_data = LeadService.get_lead(tenant_id, lead_id)
        return render_template("leads/form.html", lead=lead_data)
    
    except NotFoundError:
        flash("Lead not found", "error")
        return redirect(url_for("leads.list_leads"))
    except Exception as e:
        logger.error(f"Error loading lead for edit: {str(e)}")
        flash("Error loading lead", "error")
        return redirect(url_for("leads.list_leads"))


@leads_bp.route("/<lead_id>", methods=["POST"])
@login_required
@tenant_required
def update_lead_form(lead_id):
    """POST /leads/<uuid> - Update lead via form submission."""
    try:
        tenant_id = g.current_user.tenant_id
        user_id = g.current_user.id
        
        # Extract form data
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        loan_amount = request.form.get("loan_amount", "").strip()
        city = request.form.get("city", "").strip()
        priority = request.form.get("priority", "").strip()
        notes = request.form.get("notes", "").strip()
        
        # Validate
        errors = []
        if not name:
            errors.append("Name is required")
        
        if errors:
            lead_data = LeadService.get_lead(tenant_id, lead_id)
            return render_template("leads/form.html", lead=lead_data, errors=errors), 400
        
        # Convert loan_amount to float
        try:
            loan_amount = float(loan_amount) if loan_amount else None
        except ValueError:
            lead_data = LeadService.get_lead(tenant_id, lead_id)
            return render_template(
                "leads/form.html",
                lead=lead_data,
                errors=["Invalid loan amount format"]
            ), 400
        
        # Build custom_data
        custom_data = {}
        if notes:
            custom_data["notes"] = notes
        
        # Call service to update
        lead_data = LeadService.update_lead(
            tenant_id=tenant_id,
            lead_id=lead_id,
            name=name,
            email=email if email else None,
            loan_amount=loan_amount,
            city=city if city else None,
            priority=priority if priority else None,
            custom_data=custom_data if custom_data else None,
            updated_by_id=user_id
        )
        
        flash("Lead updated successfully", "success")
        return redirect(url_for("leads.view_lead", lead_id=lead_id))
    
    except NotFoundError:
        flash("Lead not found", "error")
        return redirect(url_for("leads.list_leads"))
    except ValidationError as e:
        logger.warning(f"Validation error updating lead: {str(e)}")
        lead_data = LeadService.get_lead(tenant_id, lead_id)
        return render_template(
            "leads/form.html",
            lead=lead_data,
            errors=[str(e)]
        ), 400
    except Exception as e:
        logger.error(f"Error updating lead: {str(e)}")
        flash("Error updating lead", "error")
        return redirect(url_for("leads.list_leads"))


@leads_bp.route("/<lead_id>", methods=["PUT"])
@login_required
@tenant_required
def update_lead(lead_id):
    """PUT /leads/<uuid> - Update lead via JSON API."""
    try:
        tenant_id = g.current_user.tenant_id
        user_id = g.current_user.id
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Call service
        lead_data = LeadService.update_lead(
            tenant_id=tenant_id,
            lead_id=lead_id,
            name=data.get("name"),
            email=data.get("email"),
            loan_amount=data.get("loan_amount"),
            city=data.get("city"),
            priority=data.get("priority"),
            custom_data=data.get("custom_data"),
            updated_by_id=user_id
        )
        
        return jsonify(lead_data), 200
    
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating lead: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# LEAD STATUS CHANGE
# ============================================================================

@leads_bp.route("/<lead_id>/status", methods=["PATCH"])
@login_required
@tenant_required
def change_lead_status(lead_id):
    """PATCH /leads/<uuid>/status - Move lead to new stage."""
    try:
        tenant_id = g.current_user.tenant_id
        user_id = g.current_user.id
        data = request.get_json()
        
        if not data or "status" not in data:
            return jsonify({"error": "Status not provided"}), 400
        
        new_status = data["status"]
        reason = data.get("reason", None)
        
        # Call service
        lead_data = LeadService.change_lead_status(
            tenant_id=tenant_id,
            lead_id=lead_id,
            new_status=new_status,
            reason=reason,
            updated_by_id=user_id
        )
        
        return jsonify(lead_data), 200
    
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error changing lead status: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# LEAD ASSIGNMENT
# ============================================================================

@leads_bp.route("/<lead_id>/assign", methods=["POST"])
@login_required
@tenant_required
def assign_lead(lead_id):
    """POST /leads/<uuid>/assign - Assign lead to agent."""
    try:
        tenant_id = g.current_user.tenant_id
        user_id = g.current_user.id
        data = request.get_json()
        
        if not data or "user_id" not in data:
            return jsonify({"error": "User ID not provided"}), 400
        
        assigned_to_id = data["user_id"]
        assignment_type = data.get("assignment_type", "MANUAL")
        
        # Call service
        lead_data = LeadService.assign_lead(
            tenant_id=tenant_id,
            lead_id=lead_id,
            user_id=assigned_to_id,
            assignment_type=assignment_type,
            updated_by_id=user_id
        )
        
        return jsonify(lead_data), 200
    
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error assigning lead: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# LEAD NOTES
# ============================================================================

@leads_bp.route("/<lead_id>/notes", methods=["POST"])
@login_required
@tenant_required
def add_lead_note(lead_id):
    """POST /leads/<uuid>/notes - Add note to lead."""
    try:
        tenant_id = g.current_user.tenant_id
        user_id = g.current_user.id
        data = request.get_json()
        
        if not data or "note_text" not in data:
            return jsonify({"error": "Note text not provided"}), 400
        
        note_text = data["note_text"]
        note_type = data.get("note_type", "CALL_LOG")
        
        # Call service
        note_data = LeadService.add_lead_note(
            tenant_id=tenant_id,
            lead_id=lead_id,
            note_text=note_text,
            note_type=note_type,
            created_by_id=user_id
        )
        
        return jsonify(note_data), 201
    
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error adding note: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# LEAD DELETION
# ============================================================================

@leads_bp.route("/<lead_id>", methods=["DELETE"])
@login_required
@tenant_required
@role_required(UserRole.TENANT_ADMIN, UserRole.BRANCH_MANAGER)
def delete_lead(lead_id):
    """DELETE /leads/<uuid> - Soft delete lead."""
    try:
        tenant_id = g.current_user.tenant_id
        user_id = g.current_user.id
        
        # Get lead first to mark as deleted
        lead = __get_lead_model(tenant_id, lead_id)
        if not lead:
            return jsonify({"error": "Lead not found"}), 404
        
        # Soft delete (mark is_deleted=True)
        lead.is_deleted = True
        lead.updated_by = user_id
        from app.extensions import db
        db.session.commit()
        
        logger.info(f"Lead deleted: {lead_id} by {user_id}")
        
        return jsonify({"message": "Lead deleted successfully"}), 200
    
    except Exception as e:
        logger.error(f"Error deleting lead: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def __get_lead_model(tenant_id, lead_id):
    """Helper to get Lead model (not dict)."""
    from app.leads.models import Lead
    return Lead.query.filter_by(
        id=lead_id,
        tenant_id=tenant_id,
        is_deleted=False
    ).first()
