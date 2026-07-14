export default {
  test: {
    environment: "happy-dom",
    environmentOptions: {
      happyDOM: {
        settings: {
          navigation: {
            disableChildFrameNavigation: true,
          },
        },
      },
    },
    include: ["tests/js/**/*.test.js"],
    globals: true,
    restoreMocks: true,
  },
};
