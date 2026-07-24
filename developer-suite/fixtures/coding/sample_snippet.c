/* Affine.Earth developer-suite fixture — text only, not a toolchain. */
int add(int a, int b) {
    return a + b;
}

int main(void) {
    return add(2, 2) == 4 ? 0 : 1;
}
