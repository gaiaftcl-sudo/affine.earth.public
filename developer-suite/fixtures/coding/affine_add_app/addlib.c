/* AffineAddApp C twin — text fixture for LLVM / coding-game narrative. */
int affine_add(int a, int b) {
    return a + b;
}

int affine_add_main(void) {
    return affine_add(2, 2) == 4 ? 0 : 1;
}
