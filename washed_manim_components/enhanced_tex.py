from manimlib import *

class Tex(SingleStringMathTex if "SingleStringMathTex" in globals() else VMobject):
    def __init__(self, *tex_strings, **kwargs):
        super().__init__(*tex_strings, **kwargs)
        self.semantic_type = "math_formula"
        self.semantic_role = "text_label"
        self.semantic_content = " ".join(map(str, tex_strings))

    def copy(self):
        new_obj = super().copy()
        new_obj.semantic_type = getattr(self, 'semantic_type', "math_formula")
        new_obj.semantic_role = getattr(self, 'semantic_role', "text_label")
        new_obj.semantic_content = getattr(self, 'semantic_content', "")
        return new_obj

# 兼容 3b1b 早期代码
class TexMobject(Tex):
    pass