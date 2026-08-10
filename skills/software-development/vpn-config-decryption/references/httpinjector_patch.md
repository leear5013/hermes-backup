# HTTPINJECTOR.py Attribute Fix

The `EHIDecryptor.execute` method references `cls.BYPASS_IVS` and `cls.STANDARD_IVS` as class attributes, but these are defined in the `EHIConstants` class, not on `EHIDecryptor` itself. This causes an `AttributeError` when trying to decrypt.

## Workaround

Before calling `EHIDecryptor.execute`, you can monkey-patch the missing attributes:

```python
from HTTPINJECTOR import EHIDecryptor, EHIConstants
EHIDecryptor.BYPASS_IVS = EHIConstants.BYPASS_IVS
EHIDecryptor.STANDARD_IVS = EHIConstants.STANDARD_IVS
```

Alternatively, modify the source code of `HTTPINJECTOR.py` to use `EHIConstants.BYPASS_IVS` and `EHIConstants.STANDARD_IVS` directly in the loop.

## Verification

After applying the patch, the decryption should proceed past the IV loop and attempt further steps (L2, XXTEA, Argon2, ChaCha20) as intended.