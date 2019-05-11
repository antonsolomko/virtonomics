import json

class Decoder(json.JSONDecoder):
    """JSON decoter
    Transforms numeral strings to numbers, including dictionaries keys.
    """
    
    def decode(self, s):
        result = super().decode(s)
        return self._decode(result)

    def _decode(self, o):
        if isinstance(o, str):
            if o == 't':
                return True
            elif o == 'f':
                return False
            else:
                try:
                    return int(o)
                except ValueError:
                    try:
                        return float(o)
                    except ValueError:
                        return o
        elif isinstance(o, dict):
            result = {}
            for k, v in o.items():
                try:
                    k = int(k)
                except ValueError:
                    pass
                result[k] = self._decode(v)
            return result
        elif isinstance(o, list):
            return [self._decode(v) for v in o]
        else:
            return o