from django import template
register = template.Library()

@register.filter
def sub(value, arg):
    """
    Filter này dùng để thực hiện phép trừ trong template.
    Ví dụ: {{ value|sub:arg }} sẽ tương đương với value - arg
    """
    try:
        # Chuyển đổi giá trị sang kiểu số để thực hiện phép toán
        return float(value) - float(arg)
    except (ValueError, TypeError):
        # Nếu giá trị không phải là số, trả về chuỗi rỗng
        return ''

@register.filter(name='add_attr')
def add_attr(field, css):
    attrs = {}
    key, val = css.split(':')
    attrs[key] = val
    return field.as_widget(attrs=attrs)