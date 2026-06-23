# Quickstart

```bash
pip install -e .
# for PDF/DOCX/HTML rich + S3
pip install -e '.[parse,s3]'

churn --version
churn drivers list
churn convert my-notes/ --out my-okf
churn convert report.pdf --chunk --out pdf-bundle   # uses unstructured if present
churn validate my-okf
churn preview my-okf
```

See README.md for S3/B2 anon, chunking, EKG roundtrips.

M005.003 stub page.