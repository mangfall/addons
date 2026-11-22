# Parked CI workflows

Move these two files back to `.github/workflows/` once the pushing token has the `workflow` scope
(`gh auth refresh -s workflow`). Until then, run the tests locally and create releases with
`gh release create vX.Y.Z mangfall-cards/app/mangfall-cards.js`.
