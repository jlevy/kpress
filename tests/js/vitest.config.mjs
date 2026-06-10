export default {
  test: {
    environment: "happy-dom",
    include: ["tests/js/**/*.test.js"],
    globals: true,
    restoreMocks: true,
  },
};
