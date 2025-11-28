module.exports = {
  output: {
    filename: '[name].[contenthash].js',
    path: path.resolve(__dirname, 'dist')
  },
  // Бесконечное кэширование для файлов с хэшем
  plugins: [
    new HtmlWebpackPlugin({
      cache: true
    })
  ]
};