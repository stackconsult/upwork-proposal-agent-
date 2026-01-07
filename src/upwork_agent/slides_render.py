from googleapiclient.discovery import Resource
from upwork_agent.schemas import SlideDeckSpec
from upwork_agent.errors import SlidesRenderError

def render_deck_to_slides(spec: SlideDeckSpec, slides_service: Resource) -> str:
    """
    Create a Google Slides presentation from SlideDeckSpec.
    Returns presentation ID.
    """
    try:
        # Create blank presentation
        presentation = slides_service.presentations().create(
            body={"title": spec.presentation_title}
        ).execute()
        pres_id = presentation["presentationId"]
        
        # Build batch requests for all slides
        requests = []
        
        for i, slide_spec in enumerate(spec.slides):
            slide_id = f"slide_{i}"
            
            # Create slide with blank layout
            requests.append({
                "createSlide": {
                    "objectId": slide_id,
                    "insertionIndex": i,
                    "slideLayout": "BLANK_LAYOUT",
                }
            })
            
            # Add white background
            requests.append({
                "updatePageProperties": {
                    "objectId": slide_id,
                    "pageProperties": {
                        "pageBackgroundFill": {
                            "solidFill": {
                                "color": {"rgbColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}
                            }
                        }
                    },
                    "fields": "pageBackgroundFill"
                }
            })
            
            # Add title
            title_box_id = f"title_{i}"
            requests.append({
                "createShape": {
                    "objectId": title_box_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "height": {"magnitude": 60, "unit": "PT"},
                            "width": {"magnitude": 720, "unit": "PT"}
                        },
                        "transform": {
                            "translateX": {"magnitude": 20, "unit": "PT"},
                            "translateY": {"magnitude": 30, "unit": "PT"}
                        }
                    }
                }
            })
            
            requests.append({
                "insertText": {
                    "objectId": title_box_id,
                    "text": slide_spec.title
                }
            })
            
            # Format title
            requests.append({
                "updateTextStyle": {
                    "objectId": title_box_id,
                    "style": {
                        "fontSize": {"magnitude": 40, "unit": "PT"},
                        "bold": True,
                        "fontFamily": "Arial"
                    },
                    "fields": "fontSize,bold,fontFamily"
                }
            })
            
            # Add subtitle if present
            if slide_spec.subtitle:
                subtitle_box_id = f"subtitle_{i}"
                requests.append({
                    "createShape": {
                        "objectId": subtitle_box_id,
                        "shapeType": "TEXT_BOX",
                        "elementProperties": {
                            "pageObjectId": slide_id,
                            "size": {
                                "height": {"magnitude": 40, "unit": "PT"},
                                "width": {"magnitude": 720, "unit": "PT"}
                            },
                            "transform": {
                                "translateX": {"magnitude": 20, "unit": "PT"},
                                "translateY": {"magnitude": 95, "unit": "PT"}
                            }
                        }
                    }
                })
                
                requests.append({
                    "insertText": {
                        "objectId": subtitle_box_id,
                        "text": slide_spec.subtitle
                    }
                })
                
                requests.append({
                    "updateTextStyle": {
                        "objectId": subtitle_box_id,
                        "style": {
                            "fontSize": {"magnitude": 24, "unit": "PT"},
                            "fontFamily": "Arial"
                        },
                        "fields": "fontSize,fontFamily"
                    }
                })
            
            # Add content sections
            content_y_offset = 150 if slide_spec.subtitle else 110
            
            for j, section in enumerate(slide_spec.sections):
                section_box_id = f"section_{i}_{j}"
                
                # Calculate content height based on type
                if section.type == "bullets":
                    content_height = len(section.content) * 30 + 20 if isinstance(section.content, list) else 60
                else:
                    content_height = 100
                
                requests.append({
                    "createShape": {
                        "objectId": section_box_id,
                        "shapeType": "TEXT_BOX",
                        "elementProperties": {
                            "pageObjectId": slide_id,
                            "size": {
                                "height": {"magnitude": content_height, "unit": "PT"},
                                "width": {"magnitude": 720, "unit": "PT"}
                            },
                            "transform": {
                                "translateX": {"magnitude": 20, "unit": "PT"},
                                "translateY": {"magnitude": content_y_offset, "unit": "PT"}
                            }
                        }
                    }
                })
                
                # Format content based on type
                if section.type == "bullets":
                    text = "\n".join(
                        f"• {bullet}" if isinstance(section.content, list) else f"• {section.content}"
                        for bullet in (section.content if isinstance(section.content, list) else [section.content])
                    )
                    font_size = 18
                else:
                    text = section.content if isinstance(section.content, str) else "\n".join(section.content)
                    font_size = 16
                
                requests.append({
                    "insertText": {
                        "objectId": section_box_id,
                        "text": text
                    }
                })
                
                # Apply formatting
                requests.append({
                    "updateTextStyle": {
                        "objectId": section_box_id,
                        "style": {
                            "fontSize": {"magnitude": font_size, "unit": "PT"},
                            "bold": section.emphasis,
                            "fontFamily": "Arial"
                        },
                        "fields": "fontSize,bold,fontFamily"
                    }
                })
                
                content_y_offset += content_height + 20
        
        # Execute batch update
        body = {"requests": requests}
        slides_service.presentations().batchUpdate(
            presentationId=pres_id,
            body=body
        ).execute()
        
        return pres_id
    
    except Exception as e:
        raise SlidesRenderError(f"Failed to render slides: {e}")
