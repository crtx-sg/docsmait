# Projects Interactive Dataframe Tables Implementation

## Overview

This document describes the implementation of interactive dataframe tables for the Projects submenus (Glossary, References, Books) using the same approach as the Design Record module.

## Changes Implemented

### 1. Backend API Updates

#### New Project Resources Update Endpoint
**File**: `backend/app/main.py`

Added new PUT endpoint for updating project resources:
```python
@app.put("/projects/{project_id}/resources/{resource_id}")
def update_project_resource(
    project_id: str,
    resource_id: str,
    resource: models.ProjectResourceCreate,
    user_id: int = Depends(auth.verify_token)
):
    """Update project resource"""
```

#### Enhanced Project Service
**File**: `backend/app/projects_service_pg.py`

Added new methods:
```python
def update_project_resource(self, resource_id: str, user_id: int, name: str = None, 
                          content: str = None, resource_type: str = None) -> Dict[str, Any]:
    """Update project resource with permission checks"""

def delete_project_resource(self, resource_id: str, user_id: int) -> Dict[str, Any]:
    """Delete project resource with permission checks (previously placeholder)"""
```

**Permission Logic**:
- Only project creators or resource uploaders can update/delete resources
- Comprehensive error handling and validation

#### Database Model Enhancement
**File**: `backend/app/db_models.py`

Added `updated_at` field to ProjectResource model:
```python
updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

**Migration Script**: `backend/migrations/add_updated_at_to_project_resources.py`
- Adds updated_at column to existing project_resources table
- Updates existing records with uploaded_at values
- Includes rollback functionality

### 2. Frontend Interactive Tables

#### New Helper Function
**File**: `frontend/pages/_Projects.py`

Added update function:
```python
def update_project_resource(project_id, resource_id, name, resource_type, content=None):
    """Update project resource via API"""
```

#### Interactive Dataframe Implementation

**Pattern Used** (similar to Design Record):
1. **Data Preparation**: Create grid data with `full_resource_data` field
2. **Display DataFrame**: Show subset of columns for table display
3. **Selection Handling**: Use session state to track selected resource
4. **Edit Form**: Inline editing form with Save/Delete/Cancel buttons
5. **State Management**: Clear session state on operations completion

### 3. Detailed Implementation for Each Resource Type

#### 📖 Glossary Resources (res_tab2)

**Features**:
- Interactive table with selection (`single-row` mode)
- Edit form with name and content fields
- Content preview in table (50 characters + "...")
- Placeholder text for glossary format: "Term 1: Definition 1\nTerm 2: Definition 2\n..."
- Session state variables: `selected_glossary_id`, `selected_glossary_data`

**Permissions**:
- Project creators can edit/delete any glossary resource
- Resource uploaders can edit/delete their own resources
- Other members can view only

#### 📄 References Resources (res_tab3)

**Features**:
- Interactive table with selection capability
- Edit form for reference description/notes
- Content preview in table
- Placeholder text: "Description or notes about this reference resource..."
- Session state variables: `selected_reference_id`, `selected_reference_data`

**Permissions**: Same as glossary resources

#### 📚 Books Resources (res_tab4)

**Features**:
- Interactive table with selection capability
- Edit form for book description/summary
- Content preview in table
- Placeholder text: "Description, notes, or summary about this book resource..."
- Session state variables: `selected_book_id`, `selected_book_data`

**Permissions**: Same as other resources

### 4. User Experience Improvements

#### Visual Enhancements
- **Content Preview**: Shows first 50 characters of content in table
- **Selection Indicator**: Clear visual feedback when row is selected
- **Responsive Layout**: Forms use 2-column layout for better organization
- **Action Buttons**: Clear Save/Delete/Cancel button arrangement

#### Interaction Flow
1. User views resources in interactive dataframe table
2. User clicks on a row to select it
3. Edit form appears below with current values populated
4. User can modify name and content
5. Save button updates via API and refreshes display
6. Delete button removes resource with confirmation
7. Cancel button clears selection without changes

#### Error Handling
- Form validation (required fields)
- API error display with descriptive messages
- Permission-based error messages
- Success notifications with visual feedback

#### Session State Management
- Tracks selected resource ID and full data
- Automatic cleanup when operations complete
- Prevents conflicts between different resource types
- Clean state management when navigating away from page

### 5. API Integration

#### Update Operation
```python
success, result = update_project_resource(
    project_id, resource.get('id'), 
    edited_name, resource_type, edited_content
)
```

#### Delete Operation
```python
success, result = delete_project_resource(project_id, resource["id"])
```

#### Response Handling
- Success: Clear selection state and refresh data via `st.rerun()`
- Failure: Display error message and maintain current state

### 6. Security & Permissions

#### Backend Security
- JWT token verification on all endpoints
- User ID extraction from token
- Resource ownership validation
- Project membership verification

#### Frontend Security
- Permission checks before showing edit options
- Clear error messages for unauthorized actions
- Hide edit/delete buttons for read-only users

#### Permission Matrix
| User Type | View | Edit Own | Delete Own | Edit Others | Delete Others |
|-----------|------|----------|------------|-------------|---------------|
| Project Creator | ✅ | ✅ | ✅ | ✅ | ✅ |
| Resource Uploader | ✅ | ✅ | ✅ | ❌ | ❌ |
| Project Member | ✅ | ❌ | ❌ | ❌ | ❌ |

### 7. Database Schema Impact

#### New Column
```sql
ALTER TABLE project_resources 
ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

UPDATE project_resources 
SET updated_at = uploaded_at 
WHERE updated_at IS NULL;
```

#### Indexing Recommendations
- Consider adding index on `updated_at` for audit queries
- Consider composite index on (`project_id`, `resource_type`, `updated_at`)

### 8. Testing Checklist

#### Manual Testing
- [x] Create resources of each type (glossary, reference, book)
- [ ] Select rows in each resource type table
- [ ] Edit resource names and content
- [ ] Save changes and verify updates
- [ ] Test delete functionality
- [ ] Test cancel operations
- [ ] Verify permission restrictions
- [ ] Test with multiple users and roles

#### Edge Cases
- [ ] Empty content handling
- [ ] Large content (>1000 characters)
- [ ] Special characters in names
- [ ] Concurrent editing by multiple users
- [ ] Session state conflicts between tabs

### 9. Future Enhancements

#### Possible Improvements
1. **Batch Operations**: Select multiple resources for bulk operations
2. **Search/Filter**: Add search functionality within resource tables
3. **Sorting**: Enable column sorting in dataframes
4. **Export**: Export resources to CSV/PDF
5. **Version History**: Track changes to resources over time
6. **Rich Text Editing**: WYSIWYG editor for content
7. **File Attachments**: Support for file uploads in resources
8. **Templates**: Predefined templates for common resource types

#### Performance Optimizations
1. **Pagination**: For projects with many resources
2. **Lazy Loading**: Load resource content only when selected
3. **Caching**: Cache resource data between selections
4. **Debounced Updates**: Prevent excessive API calls during editing

## Migration Instructions

### For Existing Deployments

1. **Run Database Migration**:
   ```bash
   cd backend
   python migrations/add_updated_at_to_project_resources.py
   ```

2. **Update Backend Code**: Deploy updated backend with new API endpoints

3. **Update Frontend Code**: Deploy updated Projects page

4. **Verify Functionality**: Test interactive tables with existing resources

### For New Deployments

The database schema will automatically include the `updated_at` column when creating tables from scratch.

## Conclusion

This implementation provides a consistent, user-friendly interface for managing project resources across all three resource types (Glossary, References, Books). The approach follows the established pattern from Design Record, ensuring consistency across the application while providing robust functionality for resource management.

The interactive dataframe tables significantly improve the user experience by allowing in-place editing without navigation, while maintaining proper permission controls and data integrity.